# Makefile to help automate tasks in bookie

BOOKIE_INI = rick.ini
BOOKIE_JS = bookie/static/js/bookie
JS_BUILD_PATH = bookie/static/js/build
JS_META_SCRIPT = scripts/js/generate_meta.py
YUIGIT = git://github.com/yui/yui3.git
YUITAG = v3.5.0pr1

js: $(JS_BUILD_PATH)/b/meta.js $(JS_BUILD_PATH)/y
clean_js:
	rm -rf $(JS_BUILD_PATH)/*
	rm -rf /tmp/yui
$(JS_BUILD_PATH)/b/meta.js: $(JS_BUILD_PATH)/b/y*-min.js
	$(JS_META_SCRIPT) -n YUI_MODULES -s $(JS_BUILD_PATH)/b/ \
		-o $(JS_BUILD_PATH)/b/meta.js \
		-x -min.js$
$(JS_BUILD_PATH)/b/y%-min.js: $(JS_BUILD_PATH)/b $(JS_BUILD_PATH)/b/y%.js
	scripts/js/jsmin_all.py $(JS_BUILD_PATH)/b
$(JS_BUILD_PATH)/b/y%.js: $(BOOKIE_JS)/y%.js
	cp $? $(JS_BUILD_PATH)/b/
$(JS_BUILD_PATH)/b:
	mkdir $(JS_BUILD_PATH)/b
$(JS_BUILD_PATH)/y:
	mkdir $(JS_BUILD_PATH)/y
	mkdir /tmp/yui
	git clone --depth 1 $(YUIGIT) /tmp/yui
	cd /tmp/yui && git checkout $(YUITAG)
	cp -r /tmp/yui/build/* $(JS_BUILD_PATH)/y
	rm -rf /tmp/yui


run: run_combo run_css run_app
run_dev: run run_livereload
run_combo:
	gunicorn -p combo.pid combo:application &
run_css:
	sass --watch bookie/static/css/bookie.scss:bookie/static/css/bookie.css &
run_app:
	paster serve --reload --pid-file=paster.pid $(BOOKIE_INI) &
run_livereload:
	livereload

stop: stop_combo stop_css stop_app
stop_dev: stop stop_livereload
stop_combo:
	kill -9 `cat combo.pid`
	rm combo.pid
stop_css:
	killall -9 sass
stop_app:
	kill -9 `cat paster.pid`
	rm paster.pid
stop_livereload:
	killall livereload

clean: clean_js

.PHONY: clean clean_js $(JS_BUILD_PATH)/b/meta.js \
	run run_dev run_combo run_css run_app run_livereload \
	stop stop_dev stop_app stop_css stop_combo stop_livereload
