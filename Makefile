export JAVA_HOME:=$(HOME)/android-studio/jbr
export ANDROID_HOME:=$(HOME)/Android/Sdk
export FORMAT_JAR=bin/google-java-format.jar
export FORMAT_JAR_URL=https://github.com/google/google-java-format/releases/download/v1.32.0/google-java-format-1.32.0-all-deps.jar
export PATH:=$(PATH):$(ANDROID_HOME)/platform-tools:$(ANDROID_HOME)/tools

DICT_RES:=android/app/src/main/res/raw/dictionary_jsonl

all: build

emulator:
	$(HOME)/Android/Sdk/emulator/emulator -avd Medium_Phone_API_36.1

build: $(DICT_RES)
	cd android && ./gradlew assembleDebug

install: $(DICT_RES)
	cd android && ./gradlew installDebug

run:
	cd android && $(ANDROID_HOME)/platform-tools/adb shell am start -n net.mdln.engita/.MainActivity

logcat:
	cd android && $(ANDROID_HOME)/platform-tools/adb logcat

test:
	cd android && ./gradlew connectedAndroidTest

$(FORMAT_JAR):
	mkdir -p bin && curl -sfL -o "$(FORMAT_JAR)" "$(FORMAT_JAR_URL)"

fmt: $(FORMAT_JAR)
	find . -name "*.java" | xargs "$(JAVA_HOME)/bin/java" -jar "$(FORMAT_JAR)" --replace

bundle: $(DICT_RES)
	@bash -c 'read -s -p "Keystore password: " KEYSTORE_PASSWORD && echo && \
	export KEYSTORE_PASSWORD && export KEY_PASSWORD=$$KEYSTORE_PASSWORD && \
	cd android && ./gradlew bundleRelease'

$(DICT_RES): dict/dictionary.jsonl
	mkdir -p $$(dirname $@) && cp -f $< $@

clean:
	rm -rf android/build android/app/src/main/res/raw/*_csv
