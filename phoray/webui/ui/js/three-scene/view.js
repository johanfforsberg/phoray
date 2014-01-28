var View;

(function () {

    /*
     Render a THREE.js scene that can be rotated, zoomed and panned.
     */

    View = function (element, onSelect) {

        var events = this.events = {
            cameraChanged: new signals.Signal(),
            sceneChanged: new signals.Signal(),
            selectionChanged: new signals.Signal()
        };

        events.cameraChanged.add(function () {
            console.log("camera chanfed");
            this.render();
        }.bind(this));

        this.onSelect = onSelect;

        this.renderer = new THREE.WebGLRenderer({antialias: false});
        this.renderer.setClearColor(0x3f3f3f);

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
        this.element = this.renderer.domElement;
        element.appendChild(this.element);
        this.element.id = "view";
        this.renderer.sortObjects = false;

        this.scene = new THREE.Scene();
        this.sceneHelpers = new THREE.Scene();
        this.helpers = {};

        this.root = new THREE.Object3D();  // the scene's objects will be added to this
        this.root.name = "root";
        this.scene.add(this.root);
        this.overlay = new THREE.Scene();
        this.selected = null;
        // var camera = this.camera = new THREE.OrthographicAspectCamera(
        //     20, view_width / view_height, 0.1, 100
        // );
        // var camera = this.camera = new THREE.OrthographicCamera(
        //     -20, 20, 10, -10, 0.1, 100
        // );

        var camera = this.camera = new THREE.PerspectiveCamera( 20, view_width/view_height, 1, 10000 );
        this.camera_offset = {x: 0, y: 0, z: 0};

        this.ray = new THREE.Raycaster();
	this.projector = new THREE.Projector();

        this.setup_lights();
        this.setup_grid();
        this.setup_input();

        this.rotate();
        this.controls = new THREE.EditorControls(camera, this.element);
	this.controls.addEventListener( 'change', function () {

            console.log("editor control change");

	    this.transformcontrols.update();
	    this.events.cameraChanged.dispatch( camera );

	}.bind(this));

        this.transformcontrols = new THREE.TransformControls(this.camera,
                                                             this.element);
	this.transformcontrols.addEventListener( 'change', function (e) {
            console.log("change", this.transformcontrols.object.path);
	    this.controls.enabled = true;
	    if ( this.transformcontrols.axis !== undefined ) {
		this.controls.enabled = false;
	    }
            this.events.sceneChanged.dispatch();
	}.bind(this));

        this.sceneHelpers.add(this.transformcontrols);
        events.sceneChanged.add(this.render.bind(this));
        //events.cameraChanged.add(this.render.bind(this));

        this.render();
    };

    View.prototype.setup_input = function () {

        var self = this;

	var getIntersects = function ( event, object ) {
	    var rect = self.element.getBoundingClientRect();
	    var x = ( event.clientX - rect.left ) / rect.width,
		y = ( event.clientY - rect.top ) / rect.height;

	    var vector = new THREE.Vector3( ( x ) * 2 - 1, - ( y ) * 2 + 1, 0.5 );
	    self.projector.unprojectVector( vector, self.camera );
	    self.ray.set( self.camera.position,
                          vector.sub( self.camera.position ).normalize() );

	    if ( object instanceof Array ) {
		return self.ray.intersectObjects( object );
	    }
	    return self.ray.intersectObject( object, true );

	};

	var onMouseDownPosition = new THREE.Vector2();
	var onMouseUpPosition = new THREE.Vector2();

	var onMouseDown = function ( event ) {

	    event.preventDefault();

	    var rect = self.element.getBoundingClientRect();
	    var x = (event.clientX - rect.left) / rect.width,
		y = (event.clientY - rect.top) / rect.height;
	    onMouseDownPosition.set( x, y );

	    document.addEventListener( 'mouseup', onMouseUp, false );

	};

	var onMouseUp = function ( event ) {

	    var rect = self.element.getBoundingClientRect(),
	        x = (event.clientX - rect.left) / rect.width,
	        y = (event.clientY - rect.top) / rect.height;
	    onMouseUpPosition.set( x, y );

	    if ( onMouseDownPosition.distanceTo( onMouseUpPosition ) == 0 ) {
		var intersects = getIntersects( event, self.root );
                console.log(intersects);
		if ( intersects.length > 0 ) {
		    var object = intersects[0].object;
                    console.log("selected object", object);
		    if ( object.userData.object !== undefined ) {
			// helper
			self.transformcontrols.attach( object.userData.object );
		    } else while (object) {
                        // may be a sub-object of an element, e.g. a mesh
                        if (object.path) {
			    self.transformcontrols.attach( object );
                            console.log("select", object.path);
                            self.onSelect(object.path);
                            break;
                        }
                        object = object.parent;
		    }
		} else {
		    self.transformcontrols.detach();
		}
		self.render();
	    }

	    document.removeEventListener( 'mouseup', onMouseUp );

	};

	var onDoubleClick = function ( event ) {

		var intersects = getIntersects( event, objects );

		if ( intersects.length > 0 && intersects[ 0 ].object === editor.selected ) {

			controls.focus( editor.selected );

		}

	};

	self.element.addEventListener( 'mousedown', onMouseDown, false );
	self.element.addEventListener( 'dblclick', onDoubleClick, false );
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

        light = new THREE.AmbientLight(0x202020);
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
        grid.name = "grid";
	//grid.renderDepth = -10;  // prevent the grid from obscuring rays
        this.scene.add(grid);
    };

    View.prototype.add = function (obj) {
        this.root.add(obj);
        this.transformcontrols.attach(obj);
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

        this.camera.position.x = 50 * Math.sin(this.theta) * Math.cos(this.phi) +
	    this.camera_offset.x;
        this.camera.position.y = 50 * Math.sin(this.phi) + this.camera_offset.y;
	this.camera.position.z = 50 * Math.cos(this.theta) * Math.cos(this.phi) +
	    this.camera_offset.z;
        this.camera.width = 50 * this.scale;
        this.camera.height = 50 * this.scale;
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
	//this.transformcontrols.update();
        // draw outlines "behind" objects
        //setVisibility(this.root, true, "outline");
	this.scene.updateMatrixWorld();
        this.transformcontrols.update();
        this.renderer.render( this.scene, this.camera );
        this.renderer.render( this.sceneHelpers, this.camera );
        // this.renderer.clear( false, true, false ); // clear depth buffer
        // setVisibility(this.root, false, "outline");
        // this.renderer.render( this.scene, this.camera );
    };


})();
