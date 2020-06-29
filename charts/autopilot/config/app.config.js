var AppConfig = {
	getBaseUrl:function() {
		return "//" + window.location.hostname + ":{{ .Values.autopilot.config.appConfigJS.backendPort }}";
	}
}
