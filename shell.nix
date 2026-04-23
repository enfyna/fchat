with import <nixpkgs> {};

mkShell {
  NIX_LD_LIBRARY_PATH = lib.makeLibraryPath [
    stdenv.cc.cc
    zlib
    ffmpeg_7
  ];
  NIX_LD = lib.fileContents "${stdenv.cc}/nix-support/dynamic-linker";

  allowUnfree = true;

  nativeBuildInputs = [
      playwright-driver.browsers
      python311Packages.playwright
  ];

  buildInputs = [ 
      python311
      espeak
      imagemagick
      ffmpeg_7
      libva
      libvdpau
      libnotify

      #cuda
      cudatoolkit
      linuxPackages.nvidia_x11
      libGLU libGL
      xorg.libXi xorg.libXmu freeglut
      xorg.libXext xorg.libX11 xorg.libXv xorg.libXrandr zlib 
      ncurses5
  ];

  shellHook = ''
    export LD_LIBRARY_PATH="$NIX_LD_LIBRARY_PATH:${pkgs.linuxPackages.nvidia_x11}/lib"
    export CUDA_PATH=${pkgs.cudatoolkit}
    export EXTRA_LDFLAGS="-L/lib -L${pkgs.linuxPackages.nvidia_x11}/lib"
    export EXTRA_CCFLAGS="-I/usr/include"
    export PLAYWRIGHT_BROWSERS_PATH=${pkgs.playwright-driver.browsers}
    export PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS=true
    . .venv/bin/activate
  '';
}
