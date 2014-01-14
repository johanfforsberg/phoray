var treedata = [
        {name: "A", children: []},
        {name: "B", children: [
            {name: "C", children: [
                {name: "D", children: []}
            ]}
        ]},
        {name: "E", children: []}
    ];

var solarsystem =
    {name: "Sol", info: {
        type: "star",
        satellites: [
            {name: "Mercury", info: {type: "planet", satellites: []}},
            {name: "Venus", info: {type: "planet", satellites: []}},
            {name: "Earth", info: {
                type: "planet",
                satellites: [{name: "Moon", info: {type: "moon"}}]}
            },
            {name: "Mars", info: {
                type: "planet",
                satellites: [{name: "Phobos", info: {type: "moon"}},
                             {name: "Deimos", info: {type: "moon"}}]}
            }
        ]}
    };


var solarTree = new DNDTree(
    document.getElementById("tree"), {
        data: solarsystem,
        childPath: "info/satellites",  // path to the children of a node

        // this function is run on each node and the result is used
        // for the HTML.
        renderNode: function(tree, node) {
            return ('<b class="' + node.info.type + '"><b>' +
                    node.name + "</b>" + " (" + node.info.type + ")");
        },

        // this function is called whenever a node is selected
        onSelect: function (path) {console.log("selected:", path);},

        // ...and this one when a node is moved
        onChange: function (patch) {
            console.log("change:", patch);
            this.update(patch);  // needed, if the tree will not be updated
                                 // by some other method.
        }
    });
