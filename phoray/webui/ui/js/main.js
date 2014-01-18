Jsonary.getData("system", function (data) {
    var meshes = {}, n_rays = 1000,
        spec_el = document.getElementById("spec");

    data.addSchema("system-schema.json");
    console.log("verify", data.validate());
    data = data.editableCopy();  // make data editable

    // Create a drag-and-drop element tree
    var tree = new DNDTree(
        document.getElementById("tree"), {
            data: data.value(),
            childPath: "args/children",
            renderNode: function (tree, node, path) {
                var container = document.createElement("div"),
                    title = document.createElement("span");
                title.textContent = node["class"];
                title.classList.add("title");
                container.appendChild(title);
                return container;
            },
            onChange: function (patch) {
                if (patch[0].op == "move") {
                    // This does not quite work yet
                    var from = patch[0].from,
                        to = patch[0].path;

                    var node = data.subPath(from),
                        nodeData = node.value();
                    var from_parent_path = from.split("/").slice(0, -1).join("/"),
                        from_parent = data.subPath(from_parent_path),
                        from_index = from.split("/").slice(-1)[0];
                    //node.remove();
                    var to_parent_path = to.split("/").slice(0, -1).join("/"),
                        to_parent = data.subPath(to_parent_path),
                        to_index = to.split("/").slice(-1)[0];
                    if (to_index == "-") {
                        if (from_parent_path == to_parent_path)
                            to_index = to_parent.length() - 1;
                        else
                            to_index = to_parent.length();
                        to = to_parent_path + "/" + to_index;
                    }

                    data.subPath(from).moveTo(to);

                    // Note: seems like there's a bug in Jsonary, in the case
                    // where a node is moved to be a sibling to its parents.
                }
            },
            onSelect: function (path) {
                console.log("path", path);
                console.log(data.subPath(path).value());
                Jsonary.render(spec_el, data.subPath(path));
                scene.selectPath(path);
            }
        }
    );

    // Some nice buttons

    document.getElementById("send-data").onclick = function (e) {
        send();
    };

    document.getElementById("add-child").onclick = function (e) {
        var path = tree.getSelectedPath();
        if (path !== undefined) {
            if (path == "/")
                path = "";
            var children = data.subPath(path + "/" + tree.childPath),
                childSchema = children.schemas();
            childSchema.createValueForIndex(0, function (value) {
                children.push(value);
            });
        }
    };

    document.getElementById("delete-selected").onclick = function (e) {
        var path = tree.getSelectedPath();
        if (path) {
            data.subPath(path).remove();
        }
    };

    document.getElementById("show-footprint").onclick = function (e) {
        var path = tree.getSelectedPath();
        if (path) {
            footprint(path);
        }
    };

    // Obtain a mesh for a given geometry specification. Also keeps
    // a cache of meshes to prevent needless recalculation.
    // TODO: prune this cache periodically, now it grows monotonically
    var get_mesh = function (spec, callback) {
        var key = JSON.stringify(spec);
        if (key in meshes)
            callback(meshes[key]);
        else {
            Backend.post("mesh", {spec: spec}, function () {
                var mesh = JSON.parse(this.responseText);
                meshes[key] = mesh;
                callback(mesh);
            });
        }
    };

    // Ask the server to trace the current system
    var trace = function (n) {
        n = n || 1000;
        var t0 = Date.now();
        Backend.get("/trace?n=" + n, null, function () {
            var data = JSON.parse(this.responseText);
            console.log("trace took " + (Date.now() - t0) + " ms.");
            console.log(data);
            scene.drawTrace(data.traces);
            var selpath = tree.getSelectedPath();
        });
    };

    // Prepare the 3D representation
    var scene = new ThreeScene(document.getElementById("scene"),
                               data.value(), meshes,
                               {childPath: "args/children",
                                positionPath: "args/position",
                                rotationPath: "args/rotation",
                                meshFunction: get_mesh,
                                onSelect: tree.selectPath});

    // Function to debounce change listener, accumulating patches
    var debounce = function (func, threshold) {
        var timeout, accum_patch = [];
        return function debounced (patch, doc) {
            var obj = this;
            accum_patch = accum_patch.concat(decode_patch(patch));
            function delayed () {
                func.apply(obj, [accum_patch, doc]);
                timeout = null;
                accum_patch = [];
            };
            if (timeout)
                clearTimeout(timeout);
            timeout = setTimeout(delayed, threshold || 100);
        };
    };

    // Takes a Jsonary patch object and returns the corresponding
    // JSON-patch.
    var decode_patch = function (patch) {
        var json_patch = [];
        patch.operations.forEach(function (o, i) {
            if (o._patchType == "move")
                json_patch.push({"op": o._patchType, "path": o._target,
                                 "value": o._value, "from": o._subject});
            else
                json_patch.push({"op": o._patchType, "path": o._subject,
                                 "value": o._value, "from": o._target});
        });
        return json_patch;
    };

    // Applies a JSON-patch on the data
    var apply_patch = function (patch, data) {
        Jsonary.batch();
        patch.forEach(function (p) {
            switch (p.op) {
            case "add":
                var parent = data.subPath(p.path).parent();
                var index = parseInt(p.path.split("/").slice(-1));
                parent.insertItem(index, p.value);
                break;
            case "replace":
                data.subPath(p.path).setValue(p.value);
                break;
            }
        });
        Jsonary.batchDone();
    };

    // Send the current data to the server
    function send() {
        Backend.post("system", data.value(), function () {
            var server_patch = JSON.parse(this.responseText);
            console.log("system patch", server_patch);
            trace(n_rays);
            if (server_patch.length == 0) {
                var t0 = Date.now();
                //tree.update(patch);   // this breaks, but why?!
                tree.setData(data.value());
                console.log("tree redraw took " + (Date.now() - t0) + " ms");
                if (scene) {
                    t0 = Date.now();
                    scene.setData(data.value());
                    console.log("scene redraw took " + (Date.now() - t0) + " ms");
                }
            } else
                apply_patch(server_patch, data);
        });
    }


    // Takes care of resizing the sidebar
    function setup_resize () {
        var sidebar = document.getElementById("sidebar"),
            scene_el = document.getElementById("scene"),
            dragbar = document.getElementById("dragbar");

        dragbar.onmousedown = function(e){

            e.preventDefault();
            document.onmousemove = function(e) {
                sidebar.style.width = e.pageX + "px";
                scene_el.style.left = e.pageX + "px";
                scene.draw();
            };
        };
        document.onmouseup = function(e) {
            document.onmousemove = null;
        };

    }
    setup_resize();

    // Setyup the footprint plot dialog
    var $footprint = $("#footprint");
    $footprint.dialog({ autoOpen: false, width: 300, height: 300 });
    $footprint.dialog("option", {title: "Footprint"});

    function plot_footprint(fpdata, path) {
        //console.log("data", element, fpdata);
        if (fpdata) {
            $footprint.empty();
            $footprint.dialog("open");
            d3plot( "#footprint", fpdata.footprint );
        }
    }

    function footprint (element) {
        console.log("get footprint", element);
        $.get("/footprint", {element: element},
              function (data) {plot_footprint(data, element);});
    };

    // Called every time the data is changed, e.g. by the user
    Jsonary.registerChangeListener(debounce(function (patch, doc) {
        // Need to debounce here, because changing class can cause
        // multiple change events in some cases.

        console.log("**CHANGE***", patch, doc);

        send();

    }, 10));

    trace(n_rays);

});
