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
{{- $registryName := .Values.ui.image.registry -}}
{{- $repositoryName := .Values.ui.image.repository -}}
{{- $tag := .Values.ui.image.tag | toString -}}
{{- printf "%s/%s:%s" $registryName $repositoryName $tag -}}
{{- end -}}

{{/*
Return the proper GATE image name
*/}}
{{- define "gate.image" -}}
{{- $registryName := .Values.gate.image.registry -}}
{{- $repositoryName := .Values.gate.image.repository -}}
{{- $tag := .Values.gate.image.tag | toString -}}
{{- printf "%s/%s:%s" $registryName $repositoryName $tag -}}
{{- end -}}

{{/*
Return the proper SAPOR image name
*/}}
{{- define "sapor.image" -}}
{{- $registryName := .Values.sapor.image.registry -}}
{{- $repositoryName := .Values.sapor.image.repository -}}
{{- $tag := .Values.sapor.image.tag | toString -}}
{{- printf "%s/%s:%s" $registryName $repositoryName $tag -}}
{{- end -}}

{{/*
Return the proper platform image name
*/}}
{{- define "platform.image" -}}
{{- $registryName := .Values.platform.image.registry -}}
{{- $repositoryName := .Values.platform.image.repository -}}
{{- $tag := .Values.platform.image.tag | toString -}}
{{- printf "%s/%s:%s" $registryName $repositoryName $tag -}}
{{- end -}}

{{/*
Return the proper dashboard image name
*/}}
{{- define "dashboard.image" -}}
{{- $registryName := .Values.dashboard.image.registry -}}
{{- $repositoryName := .Values.dashboard.image.repository -}}
{{- $tag := .Values.dashboard.image.tag | toString -}}
{{- printf "%s/%s:%s" $registryName $repositoryName $tag -}}
{{- end -}}

{{/*
Return the proper sapor-db image name
*/}}
{{- define "db.image" -}}
{{- $registryName := .Values.db.image.registry -}}
{{- $repositoryName := .Values.db.image.repository -}}
{{- $tag := .Values.db.image.tag | toString -}}
{{- printf "%s/%s:%s" $registryName $repositoryName $tag -}}
{{- end -}}

{{/*
Return the proper visibility image name
*/}}
{{- define "visibility.image" -}}
{{- $registryName := .Values.visibility.image.registry -}}
{{- $repositoryName := .Values.visibility.image.repository -}}
{{- $tag := .Values.visibility.image.tag | toString -}}
{{- printf "%s/%s:%s" $registryName $repositoryName $tag -}}
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
