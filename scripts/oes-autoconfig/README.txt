# Script to automatically configure OES in an unrestricted environment

    If auto configuration is not required due to any reasons, it can 
    be disabled via an option "autoConfiguration" in values.yaml of oes

    This script is put into an image opsmx11/oes-init:<tag>

    Use below docker commands to create and publish the image

	docker build --no-cache -t opsmx11/oes-init:<tag> -f Dockerfile .
	docker push opsmx11/oes-init:<tag>

    Ensure to update the image tag in values.yaml of oes helm chart
