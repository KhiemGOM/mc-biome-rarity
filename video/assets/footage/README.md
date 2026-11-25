# Filmed footage (seed 279, Minecraft Java 26.3)

[`SHOTS.md`](SHOTS.md) names the best clip for each biome, rates it, and notes which other takes to skip. It is a copy of `D:\Coding\Minecraft\mc-capture\shots\SHOTS.md`. The clips stay in that folder and are not committed (about 100 MB each). Files named `SPOILER_*` show mushroom fields: keep the prefix until the reveal.

## How the footage was made

- **Instance:** a separate game folder, `D:\Coding\Minecraft\mc-capture`, started with `start-capture.ps1` (portablemc, JDK 25, offline user `Capture`, 1920x1080). It does not use the normal `.minecraft` folder. The world is `capture279`.
- **Game and mods:** Fabric 26.3 with Fabric API and:
  - **MCPFabric**, a local bridge on 127.0.0.1 used to run commands, teleport, read blocks and click in-game screens.
  - **Flashback**, which records replays and renders the camera paths to video.
  - **Sodium**, for rendering performance.
  - **capturectl**, our own small mod (`mc-capture\mod`). It reads a command file to start and finish recordings, open replays, set camera path keyframes, hide the HUD and export, and it writes back a status file.
- **Driver:** `mc-capture\tools\shoot.mjs` (`node shoot.mjs record|export|all [name]`) records each spot live, adds a 9 keyframe camera path (most are orbits) and exports at 1920x1080, 60 fps. No mouse, keyboard or desktop screenshots are used.
- **Private Java temp dir fix:** early launches crashed in Java's `Selector.open()` with `java.net.SocketException: Invalid argument: connect`. The fix is to give the game its own temp folder through `-Djava.io.tmpdir` and `-Djdk.net.unixdomain.tmpdir`, both set to `D:\Coding\Minecraft\mc-capture\tmp`. `start-capture.ps1` also sets `-Djava.net.preferIPv4Stack=true`.
