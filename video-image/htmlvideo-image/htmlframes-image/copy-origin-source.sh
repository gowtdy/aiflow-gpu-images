#!/bin/bash

echo "copy origin source"
origin_source_path=/Users/gowtd/work/src/open/video/hyperframes
build_assets_path=build_assets
target_path=${build_assets_path}/hyperframes
bak_path=hyperframe_bak
echo "mv ${target_path} ${bak_path}"
mv ${target_path} ${bak_path}

echo "mkdir -p ${target_path}"
mkdir -p ${target_path}
echo "copy packages"
echo "cp -r ${origin_source_path}/packages ${target_path}"
cp -r ${origin_source_path}/packages ${target_path}

echo "copy registry"
echo "cp -r ${origin_source_path}/registry ${target_path}"
cp -r ${origin_source_path}/registry ${target_path}

echo "copy skills"
echo "mkdir -p ${target_path}/skills"
mkdir -p ${target_path}/skills
cp -r ${origin_source_path}/skills/hyperframes-cli ${target_path}/skills
cp -r ${origin_source_path}/skills/hyperframes-core ${target_path}/skills
cp -r ${origin_source_path}/skills/hyperframes-creative ${target_path}/skills
mkdir -p ${build_assets_path}/scripts/lib
cp ${origin_source_path}/skills/faceless-explainer/scripts/build-frame.mjs ${build_assets_path}/scripts/
cp ${origin_source_path}/skills/faceless-explainer/scripts/lib/tokens.mjs ${build_assets_path}/scripts/lib/
cp ${origin_source_path}/bun.lock ${origin_source_path}/package.json ${origin_source_path}/CLAUDE.md ${origin_source_path}/AGENTS.md ${target_path}

echo "patch telemetry"
bash modify/patch-telemetry.sh
echo "disable auto update"
python3 modify/disable-auto-update.py
echo "remove creation workflows"
python3 modify/remove-creation-workflows.py
