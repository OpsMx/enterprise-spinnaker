{{- define "imagePullSecret" }}
{{- with .Values.imageCredentials }}
{{- printf "{\"auths\":{\"%s\":{\"username\":\"%s\",\"password\":\"%s\",\"email\":\"%s\",\"auth\":\"%s\"}}}" .registry .username .password .email (printf "%s:%s" .username .password | b64enc) | b64enc }}
{{- end }}
{{- end }}

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
Return the proper OpsMx-DB image name
*/}}
{{- define "opsmxdb.image" -}}
{{- $registryName := .Values.opsmxdb.image.registry -}}
{{- $repositoryName := .Values.opsmxdb.image.repository -}}
{{- $tag := .Values.opsmxdb.image.tag | toString -}}
{{- printf "%s/%s:%s" $registryName $repositoryName $tag -}}
{{- end -}}
