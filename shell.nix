{
  description = "Development shell for LinkedIn Easy Apply Bot";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";  # Change to aarch64-linux if you are on ARM
      pkgs = nixpkgs.legacyPackages.${system};
    in
    {
      devShells.${system}.default = pkgs.mkShell {
        packages = with pkgs; [
          python312
          python312Packages.pip
          chromium
          chromedriver
        ];

        shellHook = ''
          echo "=== Nix Development Shell Loaded ==="
          echo "Chromium binary: $(which chromium)"
          echo "Chromedriver: $(which chromedriver)"
          echo "Python: $(which python)"
          export CHROME_BIN="$(which chromium)"
        '';
      };
    };
}