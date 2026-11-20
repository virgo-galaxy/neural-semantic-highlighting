import type { PackManifest } from "@nsh/core";

export interface ModelAsset {
  id: string;
  manifest: PackManifest;
  sha256: string;
  bytes: number;
  path: string;
  metadata: { sha256: string; path: string };
  dependencies: readonly string[];
}

export const modelAssets: readonly ModelAsset[] = [
  {
    id: "typescript",
    manifest: {
      id: "typescript",
      documentKinds: [
        {
          id: "javascript",
          extensions: [".js"],
        },
        {
          id: "javascript-esm",
          extensions: [".mjs"],
        },
        {
          id: "javascript-commonjs",
          extensions: [".cjs"],
        },
        {
          id: "jsx",
          extensions: [".jsx"],
        },
        {
          id: "typescript",
          extensions: [".ts"],
        },
        {
          id: "typescript-esm",
          extensions: [".mts"],
        },
        {
          id: "typescript-commonjs",
          extensions: [".cts"],
        },
        {
          id: "tsx",
          extensions: [".tsx"],
        },
        {
          id: "typescript-declaration",
          extensions: [".d.ts"],
        },
        {
          id: "typescript-esm-declaration",
          extensions: [".d.mts"],
        },
        {
          id: "typescript-commonjs-declaration",
          extensions: [".d.cts"],
        },
      ],
    },
    sha256: "9d067b497f970f343c2bb063fe70748dcf3d4c841c9baeb6f9ab68fb741ebb33",
    bytes: 3614184,
    path: "v1/typescript/9d067b497f970f343c2bb063fe70748dcf3d4c841c9baeb6f9ab68fb741ebb33.onnx",
    metadata: {
      sha256: "2da94425e5bd9cb2e5f3f7d2bc4f740a702ca8034e81a1a173528dfd6c72a801",
      path: "v1/typescript/2da94425e5bd9cb2e5f3f7d2bc4f740a702ca8034e81a1a173528dfd6c72a801.json",
    },
    dependencies: [],
  },
  {
    id: "go",
    manifest: {
      id: "go",
      documentKinds: [
        {
          id: "go",
          extensions: [".go"],
        },
      ],
    },
    sha256: "d61b4838333ad5109201b833786292542691ae4210b0e24c86d7f90d3fabf827",
    bytes: 3600611,
    path: "v1/go/d61b4838333ad5109201b833786292542691ae4210b0e24c86d7f90d3fabf827.onnx",
    metadata: {
      sha256: "358308e494ea19a86e6c6546504b528da561d4f462254a18ae4a52b1df14fbfb",
      path: "v1/go/358308e494ea19a86e6c6546504b528da561d4f462254a18ae4a52b1df14fbfb.json",
    },
    dependencies: [],
  },
  {
    id: "css",
    manifest: {
      id: "css",
      documentKinds: [
        {
          id: "css",
          extensions: [".css"],
        },
        {
          id: "scss",
          extensions: [".scss"],
        },
        {
          id: "less",
          extensions: [".less"],
        },
      ],
    },
    sha256: "65f244b0447b3d2251bfecad9ba8bcf092a9aa45c01f1f3e4ff47031c61f94bc",
    bytes: 3599063,
    path: "v1/css/65f244b0447b3d2251bfecad9ba8bcf092a9aa45c01f1f3e4ff47031c61f94bc.onnx",
    metadata: {
      sha256: "69011087bbdbeebeabf6333b5f45343790a56ee49aec5954de0283ec7b047147",
      path: "v1/css/69011087bbdbeebeabf6333b5f45343790a56ee49aec5954de0283ec7b047147.json",
    },
    dependencies: [],
  },
  {
    id: "html",
    manifest: {
      id: "html",
      documentKinds: [
        {
          id: "html",
          extensions: [".html", ".htm"],
        },
      ],
    },
    sha256: "f3da38afbf1f52497720ec9dca0f2da810bc991c443d1167cf838700c22fb18d",
    bytes: 3596999,
    path: "v1/html/f3da38afbf1f52497720ec9dca0f2da810bc991c443d1167cf838700c22fb18d.onnx",
    metadata: {
      sha256: "bcb73030b53dc32deb774cb4cd372e3054a3099f1640ae89386a899f075954eb",
      path: "v1/html/bcb73030b53dc32deb774cb4cd372e3054a3099f1640ae89386a899f075954eb.json",
    },
    dependencies: ["typescript", "css"],
  },
  {
    id: "vue",
    manifest: {
      id: "vue",
      documentKinds: [
        {
          id: "vue",
          extensions: [".vue"],
        },
      ],
    },
    sha256: "b39e066ce627bd289e2724e1530bc9d9c2b55f3024f8e7fe3625a0c7b4303eaa",
    bytes: 3600095,
    path: "v1/vue/b39e066ce627bd289e2724e1530bc9d9c2b55f3024f8e7fe3625a0c7b4303eaa.onnx",
    metadata: {
      sha256: "a9e6551a01c3070ddcb84587d6b19be576ed94129dadbf3ac82eae645a2884c1",
      path: "v1/vue/a9e6551a01c3070ddcb84587d6b19be576ed94129dadbf3ac82eae645a2884c1.json",
    },
    dependencies: ["typescript", "css"],
  },
  {
    id: "python",
    manifest: {
      id: "python",
      documentKinds: [
        {
          id: "python",
          extensions: [".py", ".pyw", ".pyi"],
        },
      ],
    },
    sha256: "e0b16ef5d329c61b8e383087ea540c3edd385ffb53615ffd91244eb8a4f3e5da",
    bytes: 3606600,
    path: "v1/python/e0b16ef5d329c61b8e383087ea540c3edd385ffb53615ffd91244eb8a4f3e5da.onnx",
    metadata: {
      sha256: "ac767874db5717eff49c5d16961eea8e99ad1a111b15c999dc5aaa583827997f",
      path: "v1/python/ac767874db5717eff49c5d16961eea8e99ad1a111b15c999dc5aaa583827997f.json",
    },
    dependencies: [],
  },
  {
    id: "bash",
    manifest: {
      id: "bash",
      documentKinds: [
        {
          id: "bash",
          extensions: [".sh", ".bash", ".zsh", ".csh", ".tcsh"],
        },
      ],
    },
    sha256: "7feadcb291685616b97a852130dc1594665dc870769c2b59eb862d89204aedc9",
    bytes: 3602472,
    path: "v1/bash/7feadcb291685616b97a852130dc1594665dc870769c2b59eb862d89204aedc9.onnx",
    metadata: {
      sha256: "4852945632366af3134a220b7a96c42ae740e3a29c626b69a8a89af89757953f",
      path: "v1/bash/4852945632366af3134a220b7a96c42ae740e3a29c626b69a8a89af89757953f.json",
    },
    dependencies: [],
  },
  {
    id: "perl",
    manifest: {
      id: "perl",
      documentKinds: [
        {
          id: "perl",
          extensions: [".pl", ".pm", ".t", ".perl"],
        },
      ],
    },
    sha256: "f639a36e13b605c829fc2f4b1f4516e99965f955c547c718dc59d7cbd62ce8c7",
    bytes: 3602832,
    path: "v1/perl/f639a36e13b605c829fc2f4b1f4516e99965f955c547c718dc59d7cbd62ce8c7.onnx",
    metadata: {
      sha256: "a6c3085bbc80b50e08ca4d69ce0fbdc51b1f3d61adea027b9e74e44fcdd40a7e",
      path: "v1/perl/a6c3085bbc80b50e08ca4d69ce0fbdc51b1f3d61adea027b9e74e44fcdd40a7e.json",
    },
    dependencies: [],
  },
  {
    id: "awk",
    manifest: {
      id: "awk",
      documentKinds: [
        {
          id: "awk",
          extensions: [".awk", ".gawk"],
        },
      ],
    },
    sha256: "5bacf9a4b573e139460e3f6aa9fd114f7bdaaac2645d464aa7b5342832b6a8f7",
    bytes: 3596483,
    path: "v1/awk/5bacf9a4b573e139460e3f6aa9fd114f7bdaaac2645d464aa7b5342832b6a8f7.onnx",
    metadata: {
      sha256: "df1f26bc42e81e4f80bcd0ed767060b8406166f202af3cfb7315d633d0ca84a7",
      path: "v1/awk/df1f26bc42e81e4f80bcd0ed767060b8406166f202af3cfb7315d633d0ca84a7.json",
    },
    dependencies: [],
  },
  {
    id: "sql",
    manifest: {
      id: "sql",
      documentKinds: [
        {
          id: "sql",
          extensions: [".sql", ".psql", ".pgsql", ".plsql"],
        },
      ],
    },
    sha256: "2c4b46a359f0fd0a56ed1d9fa4ef49f437df38a3384bcf741149d6cbc0300c7b",
    bytes: 3601800,
    path: "v1/sql/2c4b46a359f0fd0a56ed1d9fa4ef49f437df38a3384bcf741149d6cbc0300c7b.onnx",
    metadata: {
      sha256: "11c1a3f7a376349ef7fbb95606d2b368be05523102347ac3cd9bc7327b4dc31f",
      path: "v1/sql/11c1a3f7a376349ef7fbb95606d2b368be05523102347ac3cd9bc7327b4dc31f.json",
    },
    dependencies: [],
  },
  {
    id: "powershell",
    manifest: {
      id: "powershell",
      documentKinds: [
        {
          id: "powershell",
          extensions: [".ps1", ".psm1", ".psd1"],
        },
      ],
    },
    sha256: "1bed4f22a5fa7e78df4739b9765e01320f29171ca7635ebd26b0e853f8480c8b",
    bytes: 3601800,
    path: "v1/powershell/1bed4f22a5fa7e78df4739b9765e01320f29171ca7635ebd26b0e853f8480c8b.onnx",
    metadata: {
      sha256: "0cc938c1d2695c59d4a5be0bb88a23742e61e98e2353c0b568c167b7d417442f",
      path: "v1/powershell/0cc938c1d2695c59d4a5be0bb88a23742e61e98e2353c0b568c167b7d417442f.json",
    },
    dependencies: [],
  },
  {
    id: "bat",
    manifest: {
      id: "bat",
      documentKinds: [
        {
          id: "bat",
          extensions: [".bat", ".cmd"],
        },
      ],
    },
    sha256: "a58387875df39b4ef4c885c7120fa47ef0f1f8fa2fcd540d15c55072c4dbcfcb",
    bytes: 3600252,
    path: "v1/bat/a58387875df39b4ef4c885c7120fa47ef0f1f8fa2fcd540d15c55072c4dbcfcb.onnx",
    metadata: {
      sha256: "9a9ed772922fb380611883c3fce10f6968a4fad7c9f9426ebe2bc6f7f2bd76f0",
      path: "v1/bat/9a9ed772922fb380611883c3fce10f6968a4fad7c9f9426ebe2bc6f7f2bd76f0.json",
    },
    dependencies: [],
  },
  {
    id: "assembly",
    manifest: {
      id: "assembly",
      documentKinds: [
        {
          id: "assembly",
          extensions: [".asm", ".ASM", ".nasm", ".masm", ".s", ".S", ".inc"],
        },
      ],
    },
    sha256: "820fa29c4a9db217c410108c3b35db5a2d42b47984e062dccf63ba87130f9a40",
    bytes: 3596999,
    path: "v1/assembly/820fa29c4a9db217c410108c3b35db5a2d42b47984e062dccf63ba87130f9a40.onnx",
    metadata: {
      sha256: "1ddd3b3c843feb743820b98fd590eb8c78e04063ed519eebd4a4e548b164f6d7",
      path: "v1/assembly/1ddd3b3c843feb743820b98fd590eb8c78e04063ed519eebd4a4e548b164f6d7.json",
    },
    dependencies: [],
  },
  {
    id: "java",
    manifest: {
      id: "java",
      documentKinds: [
        {
          id: "java",
          extensions: [".java"],
        },
      ],
    },
    sha256: "fbfbb673f46cef48f67037d450239d6eb48be429b204a27038c783a654490a9e",
    bytes: 3604380,
    path: "v1/java/fbfbb673f46cef48f67037d450239d6eb48be429b204a27038c783a654490a9e.onnx",
    metadata: {
      sha256: "ed7ca50fca6f6616d9415bc51c3d70c5a5f79043f3a5b4ffb53640cb1616dad1",
      path: "v1/java/ed7ca50fca6f6616d9415bc51c3d70c5a5f79043f3a5b4ffb53640cb1616dad1.json",
    },
    dependencies: [],
  },
  {
    id: "csharp",
    manifest: {
      id: "csharp",
      documentKinds: [
        {
          id: "csharp",
          extensions: [".cs"],
        },
      ],
    },
    sha256: "9eb62add245223af203410cacf4efc3f92edf1cbdd3494598801cd2cb1c60e70",
    bytes: 3604896,
    path: "v1/csharp/9eb62add245223af203410cacf4efc3f92edf1cbdd3494598801cd2cb1c60e70.onnx",
    metadata: {
      sha256: "ffbbc54b8c5b2e04afa69df76b5457e4f662c38fb626232425e15f86dfe97e43",
      path: "v1/csharp/ffbbc54b8c5b2e04afa69df76b5457e4f662c38fb626232425e15f86dfe97e43.json",
    },
    dependencies: [],
  },
  {
    id: "c",
    manifest: {
      id: "c",
      documentKinds: [
        {
          id: "c",
          extensions: [".c", ".h"],
        },
      ],
    },
    sha256: "6a599c8809d88458e626312753ee8844d81a71882404afd367ea6f464abfc68c",
    bytes: 3599063,
    path: "v1/c/6a599c8809d88458e626312753ee8844d81a71882404afd367ea6f464abfc68c.onnx",
    metadata: {
      sha256: "90bac5747e2e9683c81401be097ba3a52d6ab104820843d2bff4523cbb5397e6",
      path: "v1/c/90bac5747e2e9683c81401be097ba3a52d6ab104820843d2bff4523cbb5397e6.json",
    },
    dependencies: [],
  },
  {
    id: "cpp",
    manifest: {
      id: "cpp",
      documentKinds: [
        {
          id: "cpp",
          extensions: [
            ".cpp",
            ".cc",
            ".cxx",
            ".c++",
            ".C",
            ".hpp",
            ".hh",
            ".hxx",
            ".h++",
            ".ipp",
            ".tpp",
          ],
        },
      ],
    },
    sha256: "6a9387d9b1ca9fafb9d870c0c47caa482b2438ea380725d6e5743111d562eb1b",
    bytes: 3604896,
    path: "v1/cpp/6a9387d9b1ca9fafb9d870c0c47caa482b2438ea380725d6e5743111d562eb1b.onnx",
    metadata: {
      sha256: "23383b58ea63f1de64c2b871acc7f3da0523427d11fc8b4e9645ffc3b4e56fcf",
      path: "v1/cpp/23383b58ea63f1de64c2b871acc7f3da0523427d11fc8b4e9645ffc3b4e56fcf.json",
    },
    dependencies: [],
  },
  {
    id: "php",
    manifest: {
      id: "php",
      documentKinds: [
        {
          id: "php",
          extensions: [".php", ".phtml"],
        },
      ],
    },
    sha256: "268ed397266150998bb7e4a7380918ff57b14b45e9bc2da663db61af6393a54b",
    bytes: 3606444,
    path: "v1/php/268ed397266150998bb7e4a7380918ff57b14b45e9bc2da663db61af6393a54b.onnx",
    metadata: {
      sha256: "58e2dd8a40ce3f7b54f41b768c9bb7ea6f6becf21615c4ee75e6b2206c3706ca",
      path: "v1/php/58e2dd8a40ce3f7b54f41b768c9bb7ea6f6becf21615c4ee75e6b2206c3706ca.json",
    },
    dependencies: ["html"],
  },
  {
    id: "svelte",
    manifest: {
      id: "svelte",
      documentKinds: [
        {
          id: "svelte",
          extensions: [".svelte"],
        },
      ],
    },
    sha256: "eabf298cd1eb07fccb5d51dac7899c4bc9c68719c77ebb15e7f95426f6234ca6",
    bytes: 3606600,
    path: "v1/svelte/eabf298cd1eb07fccb5d51dac7899c4bc9c68719c77ebb15e7f95426f6234ca6.onnx",
    metadata: {
      sha256: "8a5fa59f71c70ed4d4d5a988869843a8c69b68ad876784564b301be24417b763",
      path: "v1/svelte/8a5fa59f71c70ed4d4d5a988869843a8c69b68ad876784564b301be24417b763.json",
    },
    dependencies: ["typescript", "css"],
  },
  {
    id: "rust",
    manifest: {
      id: "rust",
      documentKinds: [
        {
          id: "rust",
          extensions: [".rs"],
        },
      ],
    },
    sha256: "569d3680bb6f9f83b22339ba6ebc58c3621b2d4935760f4775efb1d5d34bb812",
    bytes: 3604896,
    path: "v1/rust/569d3680bb6f9f83b22339ba6ebc58c3621b2d4935760f4775efb1d5d34bb812.onnx",
    metadata: {
      sha256: "9399c696d0923b216af699794d7f5e2e027e6eacbac6c65db82beefeab17cdc0",
      path: "v1/rust/9399c696d0923b216af699794d7f5e2e027e6eacbac6c65db82beefeab17cdc0.json",
    },
    dependencies: [],
  },
  {
    id: "zig",
    manifest: {
      id: "zig",
      documentKinds: [
        {
          id: "zig",
          extensions: [".zig"],
        },
      ],
    },
    sha256: "fc188499ced1a08faa3bf3d900b7eebe1403d52ae5a718f21f0f31491071e377",
    bytes: 3600095,
    path: "v1/zig/fc188499ced1a08faa3bf3d900b7eebe1403d52ae5a718f21f0f31491071e377.onnx",
    metadata: {
      sha256: "84ba47c9a79be4cbee0980af7b740bd64c25b3b3a10124952960f9fdd51125a0",
      path: "v1/zig/84ba47c9a79be4cbee0980af7b740bd64c25b3b3a10124952960f9fdd51125a0.json",
    },
    dependencies: [],
  },
  {
    id: "dart",
    manifest: {
      id: "dart",
      documentKinds: [
        {
          id: "dart",
          extensions: [".dart"],
        },
      ],
    },
    sha256: "64b79f1fe5941e4f505e8936161067c5bc5af2ceb16083502b4499f03a0bbdc8",
    bytes: 3601643,
    path: "v1/dart/64b79f1fe5941e4f505e8936161067c5bc5af2ceb16083502b4499f03a0bbdc8.onnx",
    metadata: {
      sha256: "7ba9d4a2dd137045d98fb55f9923c6001a194d989457d78a1b314b51f80a6f1a",
      path: "v1/dart/7ba9d4a2dd137045d98fb55f9923c6001a194d989457d78a1b314b51f80a6f1a.json",
    },
    dependencies: [],
  },
  {
    id: "swift",
    manifest: {
      id: "swift",
      documentKinds: [
        {
          id: "swift",
          extensions: [".swift"],
        },
      ],
    },
    sha256: "87e8e3a76f6f49c7bd98ccd42d5fb2896800e2d56c6cda2eeea1d31a08e3f6e8",
    bytes: 3601643,
    path: "v1/swift/87e8e3a76f6f49c7bd98ccd42d5fb2896800e2d56c6cda2eeea1d31a08e3f6e8.onnx",
    metadata: {
      sha256: "a16b0b832d917b7d8909a73ef3de14efdf483c2368d1ec81278308e46cc2c8d4",
      path: "v1/swift/a16b0b832d917b7d8909a73ef3de14efdf483c2368d1ec81278308e46cc2c8d4.json",
    },
    dependencies: [],
  },
  {
    id: "kotlin",
    manifest: {
      id: "kotlin",
      documentKinds: [
        {
          id: "kotlin",
          extensions: [".kt", ".kts"],
        },
      ],
    },
    sha256: "ff2602ce8898e44772fde9b17201f636551478d173e8b7971026ea29b8e40458",
    bytes: 3605412,
    path: "v1/kotlin/ff2602ce8898e44772fde9b17201f636551478d173e8b7971026ea29b8e40458.onnx",
    metadata: {
      sha256: "1e8050da74bba07b98e9ec6eb719d1f6ae6028a587c444c3e4ddb43123217072",
      path: "v1/kotlin/1e8050da74bba07b98e9ec6eb719d1f6ae6028a587c444c3e4ddb43123217072.json",
    },
    dependencies: [],
  },
  {
    id: "r",
    manifest: {
      id: "r",
      documentKinds: [
        {
          id: "r",
          extensions: [".R", ".r", ".Rprofile"],
        },
      ],
    },
    sha256: "73236e36696fdf9b14d5bfe3bc7b4743a51b4b3b037d01a0961556e5aa4b1a4b",
    bytes: 3601643,
    path: "v1/r/73236e36696fdf9b14d5bfe3bc7b4743a51b4b3b037d01a0961556e5aa4b1a4b.onnx",
    metadata: {
      sha256: "1df81a4e306ee910b68ae1fa6f8d294f5a7ba6c943acc7d0ab42cfa483f8fad0",
      path: "v1/r/1df81a4e306ee910b68ae1fa6f8d294f5a7ba6c943acc7d0ab42cfa483f8fad0.json",
    },
    dependencies: [],
  },
  {
    id: "scala",
    manifest: {
      id: "scala",
      documentKinds: [
        {
          id: "scala",
          extensions: [".scala", ".sc", ".sbt"],
        },
      ],
    },
    sha256: "62c85720d5a92b21b9feedb57e53eb440cf576202a5ccfa6db915cc4f3fcaa4a",
    bytes: 3607632,
    path: "v1/scala/62c85720d5a92b21b9feedb57e53eb440cf576202a5ccfa6db915cc4f3fcaa4a.onnx",
    metadata: {
      sha256: "052631bc2c5d96f1b6fa23b59bfbe0363f58f91e0f380209b4ad4f7a8587b275",
      path: "v1/scala/052631bc2c5d96f1b6fa23b59bfbe0363f58f91e0f380209b4ad4f7a8587b275.json",
    },
    dependencies: [],
  },
  {
    id: "ruby",
    manifest: {
      id: "ruby",
      documentKinds: [
        {
          id: "ruby",
          extensions: [".rb", ".rake", ".gemspec", "Gemfile", "Rakefile"],
        },
      ],
    },
    sha256: "f785323f41b65d34e377be50bb1762b81acc69bd1acccbaedea9dacac362e40e",
    bytes: 3607632,
    path: "v1/ruby/f785323f41b65d34e377be50bb1762b81acc69bd1acccbaedea9dacac362e40e.onnx",
    metadata: {
      sha256: "fb449c9e9fc9f67c7260982152347d1abfd81b6d8a7a8ac2de7e4af5245030e7",
      path: "v1/ruby/fb449c9e9fc9f67c7260982152347d1abfd81b6d8a7a8ac2de7e4af5245030e7.json",
    },
    dependencies: [],
  },
  {
    id: "lua",
    manifest: {
      id: "lua",
      documentKinds: [
        {
          id: "lua",
          extensions: [".lua"],
        },
      ],
    },
    sha256: "aef00225244753e9e70930a9f0d274e62c0c18b094465fa2a7ce6a7a7b341cc6",
    bytes: 3605412,
    path: "v1/lua/aef00225244753e9e70930a9f0d274e62c0c18b094465fa2a7ce6a7a7b341cc6.onnx",
    metadata: {
      sha256: "7e375df163c737e17ed45cf2bc89897bb11412f8922b4094e0da7e733e28a06f",
      path: "v1/lua/7e375df163c737e17ed45cf2bc89897bb11412f8922b4094e0da7e733e28a06f.json",
    },
    dependencies: [],
  },
  {
    id: "json",
    manifest: {
      id: "json",
      documentKinds: [
        {
          id: "json",
          extensions: [".json"],
        },
        {
          id: "jsonc",
          extensions: [".jsonc", ".code-workspace"],
        },
      ],
    },
    sha256: "8dbb80ef311ca76327e6e329f7ad2fb53e1a8ed3ea07783b1f5a458330bccdbf",
    bytes: 3601643,
    path: "v1/json/8dbb80ef311ca76327e6e329f7ad2fb53e1a8ed3ea07783b1f5a458330bccdbf.onnx",
    metadata: {
      sha256: "ca7475857aa322a91096cd764576fee30796334f7ee1679b453036a69d307d5e",
      path: "v1/json/ca7475857aa322a91096cd764576fee30796334f7ee1679b453036a69d307d5e.json",
    },
    dependencies: [],
  },
  {
    id: "yaml",
    manifest: {
      id: "yaml",
      documentKinds: [
        {
          id: "yaml",
          extensions: [".yaml", ".yml"],
        },
      ],
    },
    sha256: "3a20c5ec6e9f46b752715f69aa04860336bf63a5bc9b1f66656646a797db68ed",
    bytes: 3601643,
    path: "v1/yaml/3a20c5ec6e9f46b752715f69aa04860336bf63a5bc9b1f66656646a797db68ed.onnx",
    metadata: {
      sha256: "85b0999d15febdeeb3d5012315af469d8292663537679bfd88240f5f6a6191b4",
      path: "v1/yaml/85b0999d15febdeeb3d5012315af469d8292663537679bfd88240f5f6a6191b4.json",
    },
    dependencies: [],
  },
  {
    id: "toml",
    manifest: {
      id: "toml",
      documentKinds: [
        {
          id: "toml",
          extensions: [".toml"],
        },
      ],
    },
    sha256: "529bc6c6d6792d763dcd542748b56f007c3188ad395bad03b0133467fb317db0",
    bytes: 3601643,
    path: "v1/toml/529bc6c6d6792d763dcd542748b56f007c3188ad395bad03b0133467fb317db0.onnx",
    metadata: {
      sha256: "1107400b2fb872065891074f25cf4b4f3cd53397e8a66557e9bb9c1742010da9",
      path: "v1/toml/1107400b2fb872065891074f25cf4b4f3cd53397e8a66557e9bb9c1742010da9.json",
    },
    dependencies: [],
  },
  {
    id: "ini",
    manifest: {
      id: "ini",
      documentKinds: [
        {
          id: "ini",
          extensions: [".ini", ".INI", ".cfg", ".CFG", ".editorconfig"],
        },
      ],
    },
    sha256: "84b39fd736b8fec07da85677cb1ad37f0bfebb4d517201da48875b6ab1e1f3ab",
    bytes: 3601643,
    path: "v1/ini/84b39fd736b8fec07da85677cb1ad37f0bfebb4d517201da48875b6ab1e1f3ab.onnx",
    metadata: {
      sha256: "e11b1291aad736af08192accba45cc42a3ca12d6d5a1c2cfdd424340c3bf29a9",
      path: "v1/ini/e11b1291aad736af08192accba45cc42a3ca12d6d5a1c2cfdd424340c3bf29a9.json",
    },
    dependencies: [],
  },
  {
    id: "dotenv",
    manifest: {
      id: "dotenv",
      documentKinds: [
        {
          id: "dotenv",
          extensions: [
            ".env",
            ".dotenv",
            ".env.example",
            ".env.sample",
            ".env.template",
            ".env.local",
            ".env.development",
            ".env.production",
            ".env.test",
            ".env.staging",
            ".env.development.local",
            ".env.production.local",
          ],
        },
      ],
    },
    sha256: "3dcdc12202c3f397c811128ca65a093e809e8bf44ef3e63386fe6448ea085c6f",
    bytes: 3601643,
    path: "v1/dotenv/3dcdc12202c3f397c811128ca65a093e809e8bf44ef3e63386fe6448ea085c6f.onnx",
    metadata: {
      sha256: "5878d9d5e7b607a2887fcdf7fb7f57fc763041cfc05d07f855ed629f1ebb7f95",
      path: "v1/dotenv/5878d9d5e7b607a2887fcdf7fb7f57fc763041cfc05d07f855ed629f1ebb7f95.json",
    },
    dependencies: [],
  },
  {
    id: "xml",
    manifest: {
      id: "xml",
      documentKinds: [
        {
          id: "xml",
          extensions: [
            ".xml",
            ".xsd",
            ".xsl",
            ".xslt",
            ".wsdl",
            ".rss",
            ".atom",
            ".plist",
            ".csproj",
            ".props",
            ".targets",
          ],
        },
        {
          id: "svg",
          extensions: [".svg"],
        },
      ],
    },
    sha256: "fb82277447d7abda93e367c42a3b2f754c6e8e6066b0ffa67490883a1eada837",
    bytes: 3601440,
    path: "v1/xml/fb82277447d7abda93e367c42a3b2f754c6e8e6066b0ffa67490883a1eada837.onnx",
    metadata: {
      sha256: "7de5a609585ac42b7d84ccbeb739f25d53548c3932ec41c39e300d492beda1b2",
      path: "v1/xml/7de5a609585ac42b7d84ccbeb739f25d53548c3932ec41c39e300d492beda1b2.json",
    },
    dependencies: [],
  },
  {
    id: "markdown",
    manifest: {
      id: "markdown",
      documentKinds: [
        {
          id: "markdown",
          extensions: [".md", ".markdown", ".mdown", ".mkd"],
        },
      ],
    },
    sha256: "abee506b9266276e1e0cf4227ceca124f6f8e36bd30f6979a74c1a5e0c602b38",
    bytes: 3599063,
    path: "v1/markdown/abee506b9266276e1e0cf4227ceca124f6f8e36bd30f6979a74c1a5e0c602b38.onnx",
    metadata: {
      sha256: "a8c40b0d89b309fc0598a815936bda312f6b14360372c51ea68c6eb420d9038c",
      path: "v1/markdown/a8c40b0d89b309fc0598a815936bda312f6b14360372c51ea68c6eb420d9038c.json",
    },
    dependencies: [],
  },
  {
    id: "dockerfile",
    manifest: {
      id: "dockerfile",
      documentKinds: [
        {
          id: "dockerfile",
          extensions: ["Dockerfile", ".dockerfile", "Containerfile", ".containerfile"],
        },
      ],
    },
    sha256: "828ef4d0cf69a788a98f450dda80e867d65a2725b0fcc994f67804c5dfcba45a",
    bytes: 3598031,
    path: "v1/dockerfile/828ef4d0cf69a788a98f450dda80e867d65a2725b0fcc994f67804c5dfcba45a.onnx",
    metadata: {
      sha256: "11970a68d68a6ee35701202ce7f700f70003a5e7f3eee3d11e157ad6ddbb4df8",
      path: "v1/dockerfile/11970a68d68a6ee35701202ce7f700f70003a5e7f3eee3d11e157ad6ddbb4df8.json",
    },
    dependencies: [],
  },
  {
    id: "makefile",
    manifest: {
      id: "makefile",
      documentKinds: [
        {
          id: "makefile",
          extensions: ["Makefile", "makefile", "GNUmakefile", ".mk", ".mak"],
        },
      ],
    },
    sha256: "dc2a671e059135f78bf04df97d8e3d5e878a84a04785a60903fb5691713d1a4e",
    bytes: 3600768,
    path: "v1/makefile/dc2a671e059135f78bf04df97d8e3d5e878a84a04785a60903fb5691713d1a4e.onnx",
    metadata: {
      sha256: "ce5dd158fdb1d4df9e0e404905626cf79e1b0caf2dd0fa796a6255feddcea360",
      path: "v1/makefile/ce5dd158fdb1d4df9e0e404905626cf79e1b0caf2dd0fa796a6255feddcea360.json",
    },
    dependencies: [],
  },
  {
    id: "graphql",
    manifest: {
      id: "graphql",
      documentKinds: [
        {
          id: "graphql",
          extensions: [".graphql", ".gql"],
        },
      ],
    },
    sha256: "966e75ac022a90ee3cf4b177ffcf0e7ce85b23775ee8d8d485af0d526ad17913",
    bytes: 3603348,
    path: "v1/graphql/966e75ac022a90ee3cf4b177ffcf0e7ce85b23775ee8d8d485af0d526ad17913.onnx",
    metadata: {
      sha256: "b47e986fad7831186a28f5ae63bb7f9c27e648210f9ceb1053d2d7aa3860b844",
      path: "v1/graphql/b47e986fad7831186a28f5ae63bb7f9c27e648210f9ceb1053d2d7aa3860b844.json",
    },
    dependencies: [],
  },
  {
    id: "protobuf",
    manifest: {
      id: "protobuf",
      documentKinds: [
        {
          id: "protobuf",
          extensions: [".proto"],
        },
      ],
    },
    sha256: "cbb5cf1492a925921e355350dbe0d2ce665228eedd7c4f0d2121a746ffab492e",
    bytes: 3602832,
    path: "v1/protobuf/cbb5cf1492a925921e355350dbe0d2ce665228eedd7c4f0d2121a746ffab492e.onnx",
    metadata: {
      sha256: "ed12def18ec9848f46a4b293c5a004864a8a873154e97a58533338ea4cad5dfc",
      path: "v1/protobuf/ed12def18ec9848f46a4b293c5a004864a8a873154e97a58533338ea4cad5dfc.json",
    },
    dependencies: [],
  },
  {
    id: "diff",
    manifest: {
      id: "diff",
      documentKinds: [
        {
          id: "diff",
          extensions: [".diff", ".patch"],
        },
      ],
    },
    sha256: "b796bb32dcfeeff7160ec42eac43f0a7f9450304675e12fb8869d52debcb05dc",
    bytes: 3598704,
    path: "v1/diff/b796bb32dcfeeff7160ec42eac43f0a7f9450304675e12fb8869d52debcb05dc.onnx",
    metadata: {
      sha256: "88248048acb0eac0d0e19ba64a16eaabe4f3dba029c8692b73110c517613befb",
      path: "v1/diff/88248048acb0eac0d0e19ba64a16eaabe4f3dba029c8692b73110c517613befb.json",
    },
    dependencies: [],
  },
];
