{{- define "imagePullSecret" }}
{{- with .Values.imageCredentials }}
{{- printf "{\"auths\":{\"%s\":{\"username\":\"%s\",\"password\":\"%s\",\"email\":\"%s\",\"auth\":\"%s\"}}}" .registry .username .password .email (printf "%s:%s" .username .password | b64enc) | b64enc }}
{{- end }}
{{- end }}

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

{{/*
Return the proper OpsMx-DB image name
*/}}
{{- define "opsmxdb.image" -}}
{{- $registryName := .Values.opsmxdb.image.registry -}}
{{- $repositoryName := .Values.opsmxdb.image.repository -}}
{{- $tag := .Values.opsmxdb.image.tag | toString -}}
{{- printf "%s/%s:%s" $registryName $repositoryName $tag -}}
{{- end -}}
