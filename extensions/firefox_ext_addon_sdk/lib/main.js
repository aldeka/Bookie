const widgets = require("widget");
const panel = require("panel");
const data = require("self").data;
const tabs = require("tabs");

exports.main = function(options, callback) {
    // the main bookie panel. This contains the bookmark submission form.
    var bPanel = panel.Panel({
        width:300,
        height:250,
        contentURL:data.url("panel.html"),
        contentScriptFile:[
            data.url("script/jquery.min.js"),
            data.url("script/panel.js"),
        ],
        onShow:function() {
            //TODO: remove the body of this function, and hook into bookie instead; kicking off bookie's load event
            this.port.emit("show", {
                currentURL:tabs.activeTab.url,
                currentTitle:tabs.activeTab.title
            });
        }   
    });

    // the bookie icon button that appears in Firefox's Add-on bar.
    var bWidget = widgets.Widget({
        id: "bookie@bmark.us",
        label: "Bookie",
        contentURL: data.url("img/logo.png"),
        panel: bPanel // click event automatically shows the panel
    });
};
