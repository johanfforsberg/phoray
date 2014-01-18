var View;

(function () {

    /*
     Render a THREE.js scene that can be rotated, zoomed and panned.
     */

    View = function (element, onSelect) {
        this.renderer = new THREE.WebGLRenderer({antialias: false});
        this.renderer.setClearColor(0x3f3f3f);

        this.onSelect = onSelect;

        this.renderer.autoClear = false;

        // Camera coodinates
        this.theta = -Math.PI / 4;
        this.start_theta = this.theta,
        this.phi = Math.PI / 6;
        this.start_phi = this.phi;
        this.mouse_start = {x: 0, y: 0};
        this.mouse_pos = {x: 0, y: 0};
        this.last_mouse_pos = {x: 0, y: 0};
        this.left_mouse_down = false;
        this.right_mouse_down = false;
        this.scale = 1;

        var view_width = element.offsetWidth,
            view_height = element.offsetHeight;
        this.renderer.setSize( view_width, view_height );
        //this.element.parentNode.replaceChild(this.renderer.domElement, this.element);
        element.appendChild(this.renderer.domElement);
        this.element = this.renderer.domElement;
        this.element.id = "view";
        this.renderer.sortObjects = false;

        this.scene = new THREE.Scene();
        this.root = new THREE.Object3D();  // the scene's objects will be added to this
        this.root.name = "root";
        this.scene.add(this.root);
        this.overlay = new THREE.Scene();
        this.selected = null;
        this.camera = new THREE.OrthographicAspectCamera(
            20, view_width / view_height, 0.1, 100
        );
	//this.camera = new THREE.PerspectiveCamera( 20, view_width/view_height, 1, 10000 );
        this.camera_offset = {x: 0, y: 0, z: 0};

	this.projector = new THREE.Projector();

        this.setup_lights();
        this.setup_grid();
        this.setup_input();

        this.rotate();
        this.render();
    };

    View.prototype.setup_lights = function () {
        var light = new THREE.DirectionalLight( 0xFFFFFF, 0.5 );
        light.position.set( 10, 0, 5 );
        light.lookAt( this.scene.position );
        this.scene.add( light );

        light = new THREE.DirectionalLight( 0xFFFFFF, 1.0 );
        light.position.set( -10, 10, 5 );
        light.lookAt( this.scene.position );
        this.scene.add( light );

        light = new THREE.DirectionalLight( 0xFFFFFF, 0.5 );
        light.position.set( 0, -10, -5 );
        light.lookAt( this.scene.position );
        this.scene.add( light );

        light = new THREE.AmbientLight(0x606060);
        this.scene.add(light);

    };

    View.prototype.setup_grid = function () {
        // Grid
        var size = 10, step = 1;
        var geometry = new THREE.Geometry();
        var material = new THREE.LineBasicMaterial( { vertexColors: THREE.VertexColors } );
        var color1 = new THREE.Color( 0x888888 ), color2 = new THREE.Color( 0x666666 );

        for ( var i = - size; i <= size; i += step ) {
	    geometry.vertices.push( new THREE.Vector3( -size, 0, i ) );
	    geometry.vertices.push( new THREE.Vector3(  size, 0, i ) );

	    geometry.vertices.push( new THREE.Vector3( i, 0, -size ) );
	    geometry.vertices.push( new THREE.Vector3( i, 0,  size ) );

	    var color = i === 0 ? color1 : color2;

	    geometry.colors.push( color, color, color, color );
        }
        var grid = new THREE.Line( geometry, material, THREE.LinePieces );
	//grid.renderDepth = -10;  // prevent the grid from obscuring rays
        this.scene.add(grid);
    };

    View.prototype.setup_input = function () {

        // TODO: this is all a hack, clean it up.

        var element = this.element, view = this;

        element.onclick = function (event) {
            if (!view.mouse_pos) {
                //view.mouse_pos = {x: event.clientX, y: event.clientY};
                var rect = element.getBoundingClientRect(),
	            pos = {x: ((event.clientX - rect.left) / rect.width) * 2 - 1,
			   y: ((event.clientY - rect.top) / rect.height) * 2 - 1},
	            vector = new THREE.Vector3(pos.x, pos.y, 0.5),
                    ray = view.projector.pickingRay( vector, view.camera ),
                    intersects = ray.intersectObject( view.root, true );
                intersects = intersects.filter(function (i) {return i.face;});
                if (intersects.length > 0) {
                    var obj = intersects[0].object.parent.parent;
                    if (view.selected != obj) {
                        view.onSelect(obj.path);
                    }
                }
            }
        };

        element.onmousedown = function (event) {
            event.preventDefault();
            var rect = element.getBoundingClientRect();
	    view.mouse_start = {x: ( (event.clientX) / rect.width ) * 2 - 1,
			        y: ( (event.clientY) / rect.height ) * 2 - 1};

            view.mouse_pos = null;

            view.start_theta = view.theta;
            view.start_phi = view.phi;

	    if (event.button == 0)
		element.onmousemove = mousemove_rotate;
	    else if (event.button)
		element.onmousemove = mousemove_pan;
        };

        element.onmouseup = element.onmouseout = function ( event ) {
	    element.onmousemove = null;
            view.left_mouse_down = view.right_mouse_down = false;
        };

        var mousemove_rotate = function ( event ) {
	    event.preventDefault();
            var rect = element.getBoundingClientRect();
	    view.mouse_pos = {x: ( (event.clientX) / rect.width ) * 2 - 1,
			      y: ( (event.clientY) / rect.height ) * 2 - 1};

	    view.rotate();
            view.render();
        };

        var mousemove_pan = function ( event ) {
	    event.preventDefault();
            var rect = element.getBoundingClientRect();
	    view.mouse_pos = {x: ( (event.clientX) / rect.width ) * 2 - 1,
			      y: ( (event.clientY) / rect.height ) * 2 - 1};
	    view.pan();
            view.render();
        };

        // helper for mousewheel events
        var hookEvent = function (element, eventName, callback) {
            if(typeof(element) == "string")
                element = document.getElementById(element);
            if(element == null)
                return;
            if(element.addEventListener)
            {
                if(eventName == 'mousewheel')
                    element.addEventListener('DOMMouseScroll', callback, false);
                element.addEventListener(eventName, callback, false);
            }
            else if(element.attachEvent)
                element.attachEvent("on" + eventName, callback);
        };

        // attach callback for mousewheel zooming
        hookEvent(element, "mousewheel", function (event) {
            event = event ? event : window.event;
            var wheelData = event.detail ? event.detail : event.wheelDelta;
            var rect = element.getBoundingClientRect();
            if (wheelData > 0)
                view.scale *= 1.1;
            else
                view.scale /= 1.1;
	    view.rotate();
            view.render();
        });
    };

    View.prototype.add = function (obj) {
        this.root.add(obj);
    };

    View.prototype.clear = function () {
        var view_width = this.element.offsetWidth,
            view_height = this.element.offsetHeight;
        this.renderer.setSize( view_width, view_height );
        for (var i in this.root.children) {
            this.root.remove(this.root.children[i]);
        }
    };

    View.prototype.rotate = function () {
	this.theta = this.start_theta - 2 * (this.mouse_pos.x - this.mouse_start.x);
	this.phi = Math.min(Math.PI/2,
                            Math.max(-Math.PI/2, this.start_phi + 2 *
                                     (this.mouse_pos.y - this.mouse_start.y)));

        this.camera.position.x = 20 * Math.sin(this.theta) * Math.cos(this.phi) +
	    this.camera_offset.x;
        this.camera.position.y = 20 * Math.sin(this.phi) + this.camera_offset.y;
	this.camera.position.z = 20 * Math.cos(this.theta) * Math.cos(this.phi) +
	    this.camera_offset.z;
        this.camera.width = 20 * this.scale;
        this.camera.height = 20 * this.scale;
        this.camera.updateProjectionMatrix();
	this.camera.lookAt( this.scene.position );
    };

    View.prototype.pan = function () {
        // FIXME: does not correctly take canvas ratio into account
	var camera_x = this.camera.position.x,
	    camera_y = this.camera.position.y,
	    camera_z = this.camera.position.z;
	this.camera.translateX(-10*this.scale * (this.mouse_pos.x - this.mouse_start.x));
	this.camera.translateY(10*this.scale * (this.mouse_pos.y - this.mouse_start.y));

 	this.scene.position.x += this.camera.position.x - camera_x;
	this.scene.position.y += this.camera.position.y - camera_y;
	this.scene.position.z += this.camera.position.z - camera_z;

	this.mouse_start = this.mouse_pos;
    };

    View.prototype.center = function (position) {
 	this.scene.position.x = position.x;
	this.scene.position.y = position.y;
	this.scene.position.z = position.z;
    };

    View.prototype.setVisibility = function (obj, name, vis) {
        setVisibility(this, obj, name, vis);
    };

    function setVisibility(root, obj, name, vis) {
        obj.traverse(function (o) {
            if (o === obj) {
                o.children.forEach(function (c) {
                    if (c.name == name)
                        c.visible = vis;
                });
            }
        });
    }

    View.prototype.render = function (mouse_coords) {
        this.renderer.clear();
        // draw outlines "behind" objects
        //setVisibility(this.root, true, "outline");
        this.renderer.render( this.scene, this.camera );
        // this.renderer.clear( false, true, false ); // clear depth buffer
        // setVisibility(this.root, false, "outline");
        // this.renderer.render( this.scene, this.camera );
    };


})();
