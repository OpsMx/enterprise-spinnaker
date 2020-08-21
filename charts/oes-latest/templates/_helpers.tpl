{{- define "imagePullSecret" }}
{{- with .Values.imageCredentials }}
{{- printf "{\"auths\":{\"%s\":{\"username\":\"%s\",\"password\":\"%s\",\"email\":\"%s\",\"auth\":\"%s\"}}}" .registry .username .password .email (printf "%s:%s" .username .password | b64enc) | b64enc }}
{{- end }}
{{- end }}

{{/*
Common labels for metadata.
*/}}
{{- define "oes.standard-labels" -}}
heritage: {{ .Release.Service | quote }}
release: {{ .Release.Name | quote }}
chart: "{{ .Chart.Name }}-{{ .Chart.Version }}"
{{- end -}}

{{/*
Return the proper UI image name
*/}}
{{- define "ui.image" -}}
{{- $registryName := .Values.oes.image.ui.registry -}}
{{- $repositoryName := .Values.oes.image.ui.repository -}}
{{- $tag := .Values.oes.image.ui.tag | toString -}}
{{- printf "%s/%s:%s" $registryName $repositoryName $tag -}}
{{- end -}}

{{/*
Return the proper GATE image name
*/}}
{{- define "gate.image" -}}
{{- $registryName := .Values.oes.image.gate.registry -}}
{{- $repositoryName := .Values.oes.image.gate.repository -}}
{{- $tag := .Values.oes.image.gate.tag | toString -}}
{{- printf "%s/%s:%s" $registryName $repositoryName $tag -}}
{{- end -}}

{{/*
Return the proper SAPOR image name
*/}}
{{- define "sapor.image" -}}
{{- $registryName := .Values.oes.image.sapor.registry -}}
{{- $repositoryName := .Values.oes.image.sapor.repository -}}
{{- $tag := .Values.oes.image.sapor.tag | toString -}}
{{- printf "%s/%s:%s" $registryName $repositoryName $tag -}}
{{- end -}}

{{/*
Return the proper platform image name
*/}}
{{- define "platform.image" -}}
{{- $registryName := .Values.oes.image.platform.registry -}}
{{- $repositoryName := .Values.oes.image.platform.repository -}}
{{- $tag := .Values.oes.image.platform.tag | toString -}}
{{- printf "%s/%s:%s" $registryName $repositoryName $tag -}}
{{- end -}}

{{/*
Return the proper dashboard image name
*/}}
{{- define "dashboard.image" -}}
{{- $registryName := .Values.oes.image.dashboard.registry -}}
{{- $repositoryName := .Values.oes.image.dashboard.repository -}}
{{- $tag := .Values.oes.image.dashboard.tag | toString -}}
{{- printf "%s/%s:%s" $registryName $repositoryName $tag -}}
{{- end -}}

{{/*
Return the proper sapor-db image name
*/}}
{{- define "oesdb.image" -}}
{{- $registryName := .Values.oesdb.image.registry -}}
{{- $repositoryName := .Values.oesdb.image.repository -}}
{{- $tag := .Values.oesdb.image.tag | toString -}}
{{- printf "%s/%s:%s" $registryName $repositoryName $tag -}}
{{- end -}}

{{/*
Common labels for metadata.
*/}}
{{- define "autopilot.standard-labels" -}}
heritage: {{ .Release.Service | quote }}
release: {{ .Release.Name | quote }}
chart: "{{ .Chart.Name }}-{{ .Chart.Version }}"
{{- end -}}

{{/*
Return the proper Autopilot image name
*/}}
{{- define "autopilot.image" -}}
{{- $registryName := .Values.autopilot.image.registry -}}
{{- $repositoryName := .Values.autopilot.image.repository -}}
{{- $tag := .Values.autopilot.image.tag | toString -}}
{{- printf "%s/%s:%s" $registryName $repositoryName $tag -}}
{{- end -}}
