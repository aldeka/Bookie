// content script, corresponds with data/panel.html

self.port.on("show", function(data) {
    console.log("populating form");
    $("#description").val(data.currentTitle);
    $("#url").val(data.currentURL);
});
