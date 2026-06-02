---
name: xcode-ios-simulator-setup
description: Set up Xcode, iOS Simulator, and HBuilderX/uni-app iOS simulator debugging on macOS. Use when installing Xcode, fixing xcode-select, checking xcodebuild or simctl, downloading iOS simulator runtimes, running uni-app to iOS Simulator in HBuilderX, or resolving HBuilderX errors such as ARM64-only simulator runtime, iOS26 simulator base install failure, missing runtimes, or no iOS simulator devices.
---

# Xcode iOS Simulator Setup

Use this skill when helping set up or repair a macOS environment for iOS Simulator, HBuilderX, or uni-app App debugging.

## Ground Rules

- Do not run project build, lint, or type-check commands unless the user asks.
- Prefer checking environment state before changing anything.
- If a command needs administrator privileges, use a macOS authorization prompt when possible:

```bash
osascript -e 'do shell script "xcode-select -s /Applications/Xcode.app/Contents/Developer" with administrator privileges'
```

- Never ask for or handle the user's password directly.

## Initial Checks

Run these first:

```bash
sw_vers
mdfind "kMDItemCFBundleIdentifier == 'com.apple.dt.Xcode'"
find /Applications ~/Applications ~/Downloads -maxdepth 2 -name 'Xcode.app' -print 2>/dev/null
xcode-select -p
xcodebuild -version
xcrun simctl list runtimes
xcrun simctl list devices available
```

Interpretation:

- `xcodebuild` saying active developer directory is `/Library/Developer/CommandLineTools` means full Xcode is installed or needed, but `xcode-select` is not pointing at it.
- `xcrun: unable to find utility "simctl"` usually means `xcode-select` is still pointing at Command Line Tools.
- `== Runtimes ==` with no iOS entries means an iOS Simulator Runtime is missing.

## Xcode App Location

If Xcode is in Downloads, move it to Applications before configuring:

```bash
pgrep -fl Xcode || true
osascript -e 'tell application "Xcode" to quit'
mv ~/Downloads/Xcode.app /Applications/Xcode.app
```

If Xcode does not quit because a first-launch prompt is blocking it, ask the user to close it or use a targeted `kill` only for Xcode processes.

Then select full Xcode:

```bash
osascript -e 'do shell script "xcode-select -s /Applications/Xcode.app/Contents/Developer" with administrator privileges'
xcodebuild -version
xcode-select -p
xcodebuild -runFirstLaunch
```

Expected path:

```text
/Applications/Xcode.app/Contents/Developer
```

## Install iOS Simulator Runtime

If no iOS runtime is installed:

```bash
xcodebuild -downloadPlatform iOS
```

Then verify:

```bash
xcrun simctl list runtimes
xcrun simctl list devices available
```

## HBuilderX iOS26 ARM64-Only Failure

HBuilderX may report:

```text
当前 iOS 模拟器调试基座无法安装到仅支持 ARM64 架构的模拟器
```

or:

```text
HBuilder调试基座无法安装到仅支持 ARM64 架构的模拟器
```

Cause: Xcode 26 / iOS 26 may install an `arm64Only` simulator runtime. HBuilderX's iOS simulator debug base can require a universal runtime with `x86_64`.

Check runtime architecture:

```bash
xcrun simctl runtime list -v
```

Bad:

```text
Supported Architectures: arm64
```

Good:

```text
Supported Architectures: x86_64, arm64
```

Fix:

```bash
xcrun simctl runtime list -v
xcrun simctl runtime delete <runtime-uuid>
xcrun simctl delete unavailable
xcodebuild -downloadPlatform iOS -architectureVariant universal
```

If the universal download says:

```text
No needed downloadables found for universal
```

then old runtime/device remnants were not fully removed. Re-run:

```bash
xcrun simctl runtime list -v
xcrun simctl list devices
xcrun simctl delete unavailable
```

Then retry:

```bash
xcodebuild -downloadPlatform iOS -architectureVariant universal
```

## Create And Boot A Simulator

After a runtime is installed, devices may be auto-created. If not, create one:

```bash
xcrun simctl list devicetypes | sed -n '1,40p'
xcrun simctl list runtimes
xcrun simctl create "iPhone 17 Pro" com.apple.CoreSimulator.SimDeviceType.iPhone-17-Pro com.apple.CoreSimulator.SimRuntime.iOS-26-3
```

Boot it:

```bash
xcrun simctl boot <device-uuid>
open /Applications/Xcode.app/Contents/Developer/Applications/Simulator.app
xcrun simctl list devices available
```

## HBuilderX Steps

After environment setup:

1. Open the uni-app project in HBuilderX.
2. Choose `运行 -> 运行到手机或模拟器 -> iOS 模拟器`.
3. If the list is stale, click refresh/update simulator list.
4. Choose the booted simulator.

If compilation succeeds but the simulator shows a blank page, check HBuilderX console for runtime errors. In uni-app App, `console.log` and errors print in the HBuilderX run console.

Common project-level App compatibility errors:

```text
ReferenceError: wx is not defined
Cannot assign to "params" because it is a constant
```

These are code compatibility problems, not Xcode installation problems.

## Useful References

- DCloud iOS simulator install and iOS26 ARM64-only note: `https://uniapp.dcloud.net.cn/tutorial/run/installSimulator.html`
- DCloud App debug guide: `https://uniapp.dcloud.net.cn/tutorial/debug/debug-app.html`
