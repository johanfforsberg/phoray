var Backend = {};

(function () {

    Backend.get = function (url, args, callback) {
        var xhr = new XMLHttpRequest(),
            data = new FormData();
        for (var key in args) {
            data.append("key", args[key]);
        }
        xhr.open("GET", url, true);
        //xhr.setRequestHeader('Content-Type', 'application/json; charset=UTF-8');
        xhr.send(data);
        if (callback) xhr.onloadend = callback;
    };

    Backend.post = function (url, data, callback) {
        var xhr = new XMLHttpRequest();
        xhr.open("POST", url, true);
        xhr.setRequestHeader('Content-Type', 'application/json; charset=UTF-8');
        xhr.send(JSON.stringify(data));
        if (callback) xhr.onloadend = callback;
    };

})();
2
