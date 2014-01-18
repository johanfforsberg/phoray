var ThreeScene;

(function () {

    ThreeScene = function (element, data, meshes, options) {
        this.element = element;
        this.data = data;
        this.meshes = meshes;
        this.trace = null;
        this.selectedPath = null;
        options = options || {};
        this.childPath = options.childPath || "children";
        this.positionPath = options.positionPath || "position";
        this.rotationPath = options.rotationPath || "rotation";
        this.meshFunction = options.meshFunction;

        this.fancyTrace = false;
        this.meshFrontColor = 0x447744,
        this.meshBackColor = 0xAA7744,
        this.onSelect = options.onSelect || function () {};
        // TODO: detect webgl!
        this.view = new View(this.element, this.onSelect);
        this.draw();
        setupGui(this);
    };

    ThreeScene.prototype.setData = function (data) {
        this.data = data;
        this.draw();
    };

    ThreeScene.prototype.updateData = function (patch) {
        jsonpatch.apply(this.data, patch);
        this.draw();
    };

    ThreeScene.prototype.draw = function () {
        if (this.data) {
            this.view.clear();
            this.view.add(createNodeObject(this, this.data, "", 0));
            if (this.selectedPath) {
                var selobj = getObjectFromPath(this, this.selectedPath);
                this.view.setVisibility(selobj, "outline", true);
            }
            if (this.traceData) {
                this.drawTrace(this.traceData);
            }
            this.view.render();
        }
    };

    ThreeScene.prototype.drawTrace = function (data) {
        this.traceData = data;
        if (this.trace)
            this.view.root.remove(this.trace);
        this.trace = makeTrace(data, null, this.fancyTrace);
        this.view.root.add(this.trace);
        this.view.render();
    };

    ThreeScene.prototype.center = function (pos) {
        this.view.center(pos);
    };

    ThreeScene.prototype.selectPath = function (path) {
        if (this.view.selected) {
            this.view.setVisibility(this.view.selected, "outline", false);
        }
        if (path) {
            //var objpath = path.split("/" + this.childPath + "/").join("/children/");
            var obj = getObjectFromPath(this, path);
            if (this.selectedPath) {
                this.view.setVisibility(getObjectFromPath(this, this.selectedPath),
                                        "outline", false);
                this.view.setVisibility(getObjectFromPath(this, this.selectedPath),
                                        "axis", false);
            }
            this.selectedPath = path;
            this.view.setVisibility(obj, "outline", true);
            this.view.setVisibility(obj, "axis", true);
            this.view.render();
        }
    };

    function setupGui(scene) {
        var gui = new dat.GUI();
        gui.remember(scene);
        gui.add(scene, 'fancyTrace').onChange(scene.draw.bind(scene));
        gui.addColor(scene, 'meshFrontColor').onChange(scene.draw.bind(scene));
        gui.addColor(scene, 'meshBackColor').onChange(scene.draw.bind(scene));
        gui.closed = true;
    };

    var radians = Math.PI / 180;

    // return a list of the children of the given node
    function getChildren (node, childPath) {
        if (node instanceof Array)
            return node;
        childPath.split("/").forEach(function (p) {
            if (node !== undefined)
                node = node[p];
        });
        return node? node.slice(0) : node;
    }
    function getObjectChildren (obj) {
        return obj.children;
    }

    // return the tree node at the given path
    function getNodeFromPath(scene, path) {
        path = path.split("/" + scene.childPath + "/").slice(1);
        var node = scene.data;
        path.forEach(function (p) {
            if (p != "-")
                node = getChildren(node, scene.childPath)[parseInt(p)];
        });
        return node;
    }

    // find the DOM element corresponding to the given path
    function getObjectFromPath(scene, path) {
        path = path.split("/" + scene.childPath + "/").slice(1);
        var obj = scene.view.root.children[0];  //.children.item(parseInt(path[0]));
        path.forEach(function (p) {
            if (obj._children)
                obj = obj._children.children[parseInt(p)];
        });
        return obj;
    }

    function getPath (node, path, separator) {
        separator = separator || "/";
        path.split(separator).forEach(function (p) {
            if (p.length > 0 && node !== undefined) {
                node = node[p];
            }
        });
        return node;
    }

    // calculate the path to the given tree node
    function getPathFromNode(scene, node) {
        var path = "";
        function search(t) {
            if (t === node)
                return "/";
            var cs = getChildren(t, scene.childPath);
            for (var i in cs) {
                var c = cs[i], p = search(c);
                if (p)
                    return "/" + scene.childPath + "/" + cs.indexOf(c) + p;
            }
        }
        path = search(scene.data);
        if (path.length > 0)
            path = path.slice(0, -1);
        return path;
    }

    function createNodeObject (scene, data, path, level) {

        var position = getPath(data, scene.positionPath),
            rotation = getPath(data, scene.rotationPath),
            axis = makeAxis(),
            obj = new THREE.Object3D();
        obj.name = data.class;
        obj.path = path;
        axis.visible = false;
        obj.add(axis);
        obj.position.set(position.x, position.y, position.z);
        obj.rotation.set(rotation.x * radians,
                         rotation.y * radians,
                         rotation.z * radians);
        if (data.args.geometry && data.args.geometry.class) {
            scene.meshFunction(data.args.geometry, function (mesh) {
                var verts = mesh ? mesh.verts : null,
                    faces = mesh? mesh.faces : null;
                if (verts && faces) {
                    obj.add(makeMesh(verts, faces,
                                     scene.meshFrontColor, scene.meshBackColor));
                    var outline = makeOutline(verts);
                    outline.renderDepth = -100;
                    outline.visible = false;
                    obj.add(outline);
                    scene.view.render();
                }
            });
        }
        var childdata = getChildren(data, scene.childPath);
        if (childdata) {
            //var childPath = this.childPath;
            var children = new THREE.Object3D();
            children.name = "children";
            childdata.forEach(function (c, i) {
                children.add(createNodeObject(
                    scene, c, path + "/" + scene.childPath + "/" + i, level + 1));
            });
            obj.add(children);
            obj._children = children;
        }

        return obj;
    }

    // Create a THREE mesh out of vertex/face lists
    function makeMesh (verts, faces, frontColor, backColor) {
        var geom = new THREE.Geometry();
        verts.forEach(function (vert) {
            geom.vertices.push(new THREE.Vector3(vert[0], vert[1], vert[2]));
        });
        faces.forEach(function (face) {
            geom.faces.push(new THREE.Face3(face[0], face[1], face[2]));
        });
        geom.computeFaceNormals();
        geom.computeVertexNormals();
        var mesh = new THREE.Object3D();
        var frontmat = new THREE.MeshLambertMaterial(
            {
                color: frontColor,
                //transparent: true,
                //opacity: 0.7,
                side: THREE.FrontSide,
                shading: THREE.SmoothShading
            });
        mesh.front = new THREE.Mesh( geom, frontmat );
        mesh.add(mesh.front);
        var backmat = new THREE.MeshLambertMaterial(
            {
                color: backColor,
                //transparent: true,
                //opacity: 0.7,
                side: THREE.BackSide,
                shading: THREE.SmoothShading
            });
        mesh.back = new THREE.Mesh( geom, backmat  );
        mesh.add(mesh.back);
        mesh.name = "mesh";

        return mesh;
    };

    // Take a list of mesh vertices and make a line running along the edges of it.
    function makeOutline (verts) {
        var geom = new THREE.Geometry(), x, y, res = 11;
        for(x = 0; x < res-1; x++)
            geom.vertices.push(new THREE.Vector3(verts[x][0], verts[x][1], verts[x][2]));
        for(x = res-1; x <= res*res; x+=res)
            geom.vertices.push(new THREE.Vector3(verts[x][0], verts[x][1], verts[x][2]));
        for(x = res*res-1; x > res*(res-1); x--)
            geom.vertices.push(new THREE.Vector3(verts[x][0], verts[x][1], verts[x][2]));
        for(x = res*(res-1); x >= 0; x-=res)
            geom.vertices.push(new THREE.Vector3(verts[x][0], verts[x][1], verts[x][2]));
        var outline = new THREE.Line(
            geom, new THREE.LineBasicMaterial({
		dashSize: .1, gapSize: .2, color: 0xFFFF88, linewidth: 3}),
            THREE.LineStrip);
        outline.name = "outline";
        outline.renderDepth = 1000;
        return outline;
    };

    // Construct a THREE object that represents an element
    // with an XYZ-axis.
    function makeAxis () {
        var axis = new THREE.Object3D(),
            origin = new THREE.Vector3(0, 0, 0),
            x1 = new THREE.Vector3(1, 0, 0),
            y1 = new THREE.Vector3(0, 1, 0),
            z1 = new THREE.Vector3(0, 0, 1),
            arrow_length = 0.15, arrow_width = 0.05;

        axis.add(new THREE.ArrowHelper(
            {x: 1, y: 0, z: 0},
            {x: 0, y: 0, z: 0},
            1, 0xFF0000, arrow_length, arrow_width));

        axis.add(new THREE.ArrowHelper(
            {x: 0, y: 1, z: 0},
            {x: 0, y: 0, z: 0},
            1, 0x00FF00, arrow_length, arrow_width));

        axis.add(new THREE.ArrowHelper(
            {x: 0, y: 0, z: 1},
            {x: 0, y: 0, z: 0},
            1, 0x0000FF, arrow_length, arrow_width));

        axis.name = "axis";
        return axis;
    };

    var color_from_string = function (s) {
        return parseInt(s.slice(1), 16);
    };

    var color_from_string_times = function (s, factor) {
        factor = factor || 1;
        var r = parseInt(s.slice(1, 3), 16),
            g = parseInt(s.slice(3, 5), 16),
            b = parseInt(s.slice(5, 7), 16);
        return ~~(r * factor) << 16 ^ ~~(g * factor) << 8 ^ ~~(b * factor);
    };

    var makeTrace = function (data, colors, fancy) {

	var traces = new THREE.Object3D(), tmpdata, start, end, geometry,
            trace, line, i, j, n, m;

        for (var src in data) {
            tmpdata = data[src];

	    // Draw succeeded rays
            geometry = new THREE.Geometry();
	    m = tmpdata.succeeded.length;
	    for (i=0; i < m; i++) {
		trace = tmpdata.succeeded[i];
		n = trace.length - 1;
                for (j=0; j < n; j++ ) {
                    if (trace[j][0] === NaN) {
                        break;
		    }
                    start = new THREE.Vector3(
                        trace[j][0], trace[j][1], trace[j][2]),
                    geometry.vertices.push(start);
		    end = new THREE.Vector3(
                        trace[j+1][0], trace[j+1][1], trace[j+1][2]);
                    geometry.vertices.push(end);
                }
            }
	    //line = new THREE.Line(geometry, self.shaderMaterial, THREE.LinePieces);
            var linemat = new THREE.LineDashedMaterial( {
                //color: color_from_string_times(colors[system], Math.random()),
                //color: color_from_string_times(colors[system]),
                color: color_from_string("#ffffff"),
                opacity: 1, linewidth: 1,
                dashSize: 1, gapSize: 0,
                //dashSize: 0.1, gapSize: 0.4,
		//blending: THREE.AdditiveBlending,
                //transparent: true
            });
            if (fancy) {
		linemat.depthTest = false;
                linemat.transparent = true;
                linemat.opacity = 1 / Math.sqrt(m);
                linemat.dashSize = 0.0002;
                linemat.gapSize = 0.001;
            }
            line = new THREE.Line(geometry, linemat, THREE.LinePieces);
	    geometry.computeLineDistances();
            traces.add(line);

	    // Draw failed rays
            geometry = new THREE.Geometry();
	    m = tmpdata.failed.length;
	    for (i=0; i < m; i++) {
		trace = tmpdata.failed[i];
		n = trace.length - 1;
                for (j=0; j<n; j++ ) {
                    if (trace[j][0] === NaN)
                        break;
                    start = new THREE.Vector3(
                        trace[j][0], trace[j][1], trace[j][2]);
                    geometry.vertices.push(start);
                    end = new THREE.Vector3(
                        trace[j+1][0], trace[j+1][1], trace[j+1][2]);
                    geometry.vertices.push(end);
                }
	    }
            line = new THREE.Line(
                geometry, new THREE.LineDashedMaterial( {
                    //color: color_from_string_times(colors[src]),
                    color: "#ff0000",
                    dashSize: 0.1,
                    gapSize: 0.05} ), THREE.LinePieces);
	    geometry.computeLineDistances();
            traces.add(line);
        }

        return traces;
    };


})();
