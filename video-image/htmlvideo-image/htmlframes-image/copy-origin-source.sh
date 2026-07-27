#!/bin/bash

echo "copy origin source"
origin_source_path=/Users/gowtd/work/src/open/video/hyperframes
build_assets_path=build_assets
target_path=${build_assets_path}/hyperframes
hyperframes_bak_path=bak/hyperframes_$(date +%Y%m%d%H%M)
if [ -e "${hyperframes_bak_path}" ]; then
  echo "rm -rf ${hyperframes_bak_path}"
  rm -rf "${hyperframes_bak_path}"
fi
echo "mv ${target_path} ${hyperframes_bak_path}"
mv ${target_path} ${hyperframes_bak_path}

script_bak_path=bak/scripts_$(date +%Y%m%d%H%M)
if [ -e "${script_bak_path}" ]; then
  echo "rm -rf ${script_bak_path}"
  rm -rf "${script_bak_path}"
fi
echo "mv ${build_assets_path}/scripts ${script_bak_path}"
mv ${build_assets_path}/scripts ${script_bak_path}

echo "mkdir -p ${target_path}"
mkdir -p ${target_path}
echo "copy packages"
echo "cp -r ${origin_source_path}/packages ${target_path}"
cp -r ${origin_source_path}/packages ${target_path}

# Monorepo build scripts (producer/cli import package-subpaths.mjs at build time).
echo "copy scripts"
echo "cp -r ${origin_source_path}/scripts/package-subpaths.mjs ${target_path}"
cp -r ${origin_source_path}/scripts/package-subpaths.mjs ${target_path}

echo "copy registry"
echo "cp -r ${origin_source_path}/registry ${target_path}"
cp -r ${origin_source_path}/registry ${target_path}

echo "copy skills"
echo "mkdir -p ${target_path}/skills"
mkdir -p ${target_path}/skills
cp -r ${origin_source_path}/skills/hyperframes-cli ${target_path}/skills
cp -r ${origin_source_path}/skills/hyperframes-core ${target_path}/skills
cp -r ${origin_source_path}/skills/hyperframes-creative ${target_path}/skills
cp -r ${origin_source_path}/skills/hyperframes-animation ${target_path}/skills
cp -r ${origin_source_path}/skills/media-use ${target_path}/skills
# restore AIFlow-owned skills (not from upstream)
if [ -d "${hyperframes_bak_path}/skills/aiflow-build-storyboard" ]; then
  cp -r "${hyperframes_bak_path}/skills/aiflow-build-storyboard" "${target_path}/skills/"
fi
if [ -d "${hyperframes_bak_path}/skills/aiflow-build-frame-visual" ]; then
  cp -r "${hyperframes_bak_path}/skills/aiflow-build-frame-visual" "${target_path}/skills/"
fi
if [ -d "${hyperframes_bak_path}/skills/aiflow-build-frame-html" ]; then
  cp -r "${hyperframes_bak_path}/skills/aiflow-build-frame-html" "${target_path}/skills/"
fi
mkdir -p ${build_assets_path}/scripts/lib
echo "cp -r ${origin_source_path}/scripts/package-subpaths.mjs ${target_path}/scripts/"
cp -r ${origin_source_path}/scripts/package-subpaths.mjs ${target_path}/scripts/
cp ${script_source_path}/skills/faceless-explainer/scripts/frame-packets.mjs ${build_assets_path}/scripts/
cp ${origin_source_path}/skills/faceless-explainer/scripts/build-frame.mjs ${build_assets_path}/scripts/
cp ${origin_source_path}/skills/faceless-explainer/scripts/lib/tokens.mjs ${build_assets_path}/scripts/lib/
cp ${origin_source_path}/skills/faceless-explainer/scripts/assemble-index.mjs ${build_assets_path}/scripts/
cp ${origin_source_path}/skills/faceless-explainer/scripts/lib/storyboard.mjs ${build_assets_path}/scripts/lib/
cp ${origin_source_path}/skills/faceless-explainer/scripts/lib/dimensions.mjs ${build_assets_path}/scripts/lib/
cp ${origin_source_path}/skills/faceless-explainer/scripts/lib/assets.mjs ${build_assets_path}/scripts/lib/
cp ${origin_source_path}/skills/faceless-explainer/scripts/transitions.mjs ${build_assets_path}/scripts/
cp ${origin_source_path}/skills/faceless-explainer/scripts/lib/transition-registry.mjs ${build_assets_path}/scripts/lib/
cp ${origin_source_path}/skills/faceless-explainer/scripts/lib/transitions.json ${build_assets_path}/scripts/lib/
cp ${origin_source_path}/skills/faceless-explainer/scripts/lib/pad-frame-duration.mjs ${build_assets_path}/scripts/lib/
cp ${origin_source_path}/bun.lock ${origin_source_path}/package.json ${origin_source_path}/CLAUDE.md ${origin_source_path}/AGENTS.md ${target_path}

cp ${script_bak_path}/run_aiflow_video_pipeline.sh ${build_assets_path}/scripts/
cp ${script_bak_path}/run_aiflow_build_skills.py ${build_assets_path}/scripts/
cp ${script_bak_path}/init_with_brief.py ${build_assets_path}/scripts/


echo "patch telemetry"
bash modify/patch-telemetry.sh
echo "disable auto update"
python3 modify/disable-auto-update.py
echo "remove creation workflows"
python3 modify/remove-creation-workflows.py
echo "patch build-frame --videodir"
python3 modify/patch-build-frame.py
echo "patch assemble-index --videodir"
python3 modify/patch-assemble-index.py
echo "patch transitions --videodir"
python3 modify/patch-transitions.py
echo "patch frame-packets container paths"
python3 modify/patch-frame-packets.py
