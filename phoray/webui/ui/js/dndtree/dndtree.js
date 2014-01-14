var DNDTree;

(function () {

    DNDTree = function (element, args) {
        this.element = element;
        console.log("DNDTree", args);
        this.data = args.data || [];
        this.renderNode = args.renderNode || function (d) {return d.name;};
        this.childPath = args.childPath || "children";
        this.onSelect = args.onSelect;
        this.onChange = args.onChange;
        this.selection = null;
        this.create();
    };

    DNDTree.prototype.create = function () {
        makeTree(this.element, this);
    };

    DNDTree.prototype.setData = function (data) {
        if (this.selection) {
            var sel_path = this.getSelectedPath();
            this.selection = null;
            console.log("previously selected", sel_path);
        }
        this.data = data;
        this.create();
        if (sel_path) {
            selectPath(this, sel_path, true);
        }
    };

    DNDTree.prototype.update = function (patch) {
        if (this.selection) {
            var sel_path = getPathFromNode(this, this.selection);
            this.selection = null;
            console.log("previously selected", sel_path);
        }
        console.log("update", patch);
        jsonpatch.apply(this.data, patch);
        // FIXME: patching the underlying data object... and then
        // just rebuilding the whole tree anyway. Improve!
        this.create();
        if (sel_path) {
            selectPath(this, sel_path, true);
        }
    };

    DNDTree.prototype.getSelectedPath = function () {
        if (this.selection)
            return getPathFromNode(this, this.selection);
    };

    DNDTree.prototype.selectPath = function (path) {
        selectPath(this, path);
    };

    // === event handlers ===

    function handleDragStart(e) {
        var patch = {op: "move", from: this.getAttribute("data")};
        e.dataTransfer.setData('text/json', JSON.stringify(patch));
        e.dataTransfer.setDragImage(this, -10, -10);
        this.classList.add("dragging");
        e.stopPropagation();
    }

    function handleDragOver(e) {
        e.preventDefault();  // Needed for drop to work.
        e.dataTransfer.dropEffect = 'move';
    }

    function handleDragEnter(e) {
        e.preventDefault();  // Also needed for drop.
        if (!checkIfDragged(this) && this.getAttribute("data")) {
            this.classList.add('over');
        }
    }

    function handleDragLeave(e) {
        if (!checkIfDragged(this))
            this.classList.remove('over');
    }

    function handleDrop(tree, e) {
        if (e.stopPropagation) {
            e.stopPropagation();
        }

        var target = e.target,
            path = target.getAttribute("data"),
            patch = JSON.parse(e.dataTransfer.getData('text/json'));
        if (path && !checkIfDragged(target)) {
            var src = patch.from.split("/"),
                src_index = parseInt(src.slice(-1)[0]),
                dest = path.split("/");
            // do we need to recalculate the path?
            if (src.length > dest.length ||
               src.length == dest.length && dest.slice(-1)[0] == "-" ||
               src_index >= parseInt(dest[src.length-1]))
                patch.path = path;
            else {
                var index = parseInt(dest[src.length-1]);
                dest[src.length-1] = Math.max(index - 1, 0);
                patch.path = dest.join("/");
            }
            if (tree.onChange) {
                tree.onChange([patch]);
            } else {
                tree.update([patch]);
            }

        } else {
            target.classList.remove("dragging");
        }

        return false;
    }

    function handleDragEnd(e) {
        this.classList.remove('dragging');
        this.classList.remove('over');
    }

    function handleClick(tree, e) {
        var path = e.target.parentNode.getAttribute("data");
        e.stopPropagation();
        selectPath(tree, path);
    }

    // === helper functions ===

    function selectPath(tree, path, silent) {
        if (tree.selection) {
            var old_path = getPathFromNode(tree, tree.selection),
                el = getElementFromPath(tree, old_path);
            el.querySelector(".description").classList.remove("selected");
        }
        var node = getNodeFromPath(tree, path);
        if (node) {
            tree.selection = node;
            el = getElementFromPath(tree, path);
            el.querySelector(".description").classList.add("selected");
            if (tree.onSelect && !silent)
                tree.onSelect(path);
        }
    }

    // calculate the path to the given tree node
    function getPathFromNode(tree, node) {
        var path = "";
        function search(t) {
            if (t === node)
                return "/";
            var cs = getChildren(t, tree.childPath);
            for (var i in cs) {
                var c = cs[i], p = search(c);
                if (p)
                    return "/" + tree.childPath + "/" + cs.indexOf(c) + p;
            }
        }
        path = search(tree.data);
        if (path.length > 1)
            path = path.slice(0, -1);
        return path;
    }

    // return the tree node at the given path
    function getNodeFromPath(tree, path) {
        path = path.split("/" + tree.childPath + "/").slice(1);
        var node = tree.data;
        path.forEach(function (p) {
            if (p != "-")
                node = getChildren(node, tree.childPath)[parseInt(p)];
        });
        return node;
    }

    // find the DOM element corresponding to the given path
    function getElementFromPath(tree, path) {
        path = path.split("/" + tree.childPath + "/").slice(1);
        var el = tree.rootElement;  //.children.item(parseInt(path[0]));
        path.forEach(function (p) {
            if (p != "-")
                el = el.querySelector(".children").children.item(parseInt(p));
        });
        return el;
    }

    // return whether the given element is being dragged
    function checkIfDragged(el) {
        while (!el.classList.contains("root")) {
            if (el.classList.contains("dragging")) {
                return true;
            }
            el = el.parentNode;
        }
        return false;
    }

    // calculate the path for a node directly after the given path
    function pathAfter(path) {
        var apath = path.split("/"),
            last = parseInt(apath.slice(-1)[0]) + 1;
        apath.splice(-1, 1, last);
        return apath.join("/");
    }

    // return a list of the children of the given node
    function getChildren (node, childPath) {
        if (node instanceof Array)
            return node;
        childPath.split("/").forEach(function (p) {
            if (node === undefined)
                return node;
            else
                node = node[p];
        });
        return node? node.slice(0) : node;
    }

    function createNodeElement (tree, data, path, level) {
        level = level || 0;

        var container = document.createElement("div"),
            before = document.createElement("div"),
            middle = document.createElement("div"),
            after = document.createElement("div"),
            description = document.createElement("div"),
            children = document.createElement("div"),
            childdata = getChildren(data, tree.childPath);

        // configure the elements
        container.classList.add("node");
        container.classList.add("level-" + level);
        container.setAttribute("draggable", true);
        container.setAttribute("data", path);  // source node path
        before.classList.add("before");
        before.setAttribute("data", path);  // insert before
        middle.classList.add("middle");
        if (childdata !== undefined)
            middle.setAttribute("data", path + "/" + tree.childPath + "/-");  // last in children
        after.classList.add("after");
        after.setAttribute("data", pathAfter(path));  // insert after
        description = tree.renderNode(tree, data, path);
        description.classList.add("description");
        children.classList.add("children");

        // put them together
        container.appendChild(before);
        container.appendChild(after);
        container.appendChild(middle);
        middle.appendChild(description);
        container.appendChild(children);

        // add event callbacks
        container.addEventListener("click", handleClick.bind(null, tree));

        container.addEventListener('dragstart', handleDragStart);
        container.addEventListener('dragend', handleDragEnd);

        middle.addEventListener('dragover', handleDragOver, true);
        middle.addEventListener('drop', handleDrop.bind(null, tree), true);
        middle.addEventListener('dragenter', handleDragEnter, true);
        middle.addEventListener('dragleave', handleDragLeave, true);

        before.addEventListener('dragover', handleDragOver, true);
        before.addEventListener('drop', handleDrop.bind(null, tree), true);
        before.addEventListener('dragenter', handleDragEnter, true);
        before.addEventListener('dragleave', handleDragLeave, true);

        after.addEventListener('dragover', handleDragOver, true);
        after.addEventListener('drop', handleDrop.bind(null, tree), true);
        after.addEventListener('dragenter', handleDragEnter, true);
        after.addEventListener('dragleave', handleDragLeave, true);

        // recurse over children, if any
        if (childdata)
            childdata.forEach(function (c, i) {
                children.appendChild(
                    createNodeElement(tree, c, path + '/' + tree.childPath + '/' + i, level + 1));
            });

        return container;
    }

    function makeTree (el, tree) {
        tree.rootElement = document.createElement("div");
        tree.rootElement.classList.add("root");
        el.innerHTML = "";
        el.appendChild(tree.rootElement);
        tree.rootElement.appendChild(createNodeElement(tree, tree.data, ""));
        // if (tree.selection) {
        //     // Restore selection
        //     var selpath = tree.getSelectedPath();
        //     console.log("selpath", selpath);
        //     var sel = getElementFromPath(tree, selpath);
        //     sel.querySelector(".description").classList.add("selected");
        // }
    }

}());
