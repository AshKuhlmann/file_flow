# Changelog

## 0.1.0 (2025-07-03)


### Features

* add logging to move_with_log ([5c6d7e2](https://github.com/AshKuhlmann/file_flow/commit/5c6d7e26a073bbc5d9136d31317607f8268440fb))
* **classifier:** extension+MIME category mapping ([6dfdfc6](https://github.com/AshKuhlmann/file_flow/commit/6dfdfc62be8349ca15c34b1c2aeaa1f169269745))
* **cli:** add Typer-based CLI app ([ad6860e](https://github.com/AshKuhlmann/file_flow/commit/ad6860edbeb274297469aa2a3f3f48cc64d0eb74))
* **dupes:** SHA-256 duplicate finder & CLI command ([d87a8c7](https://github.com/AshKuhlmann/file_flow/commit/d87a8c795e206cdd289b5be65b18fae6223f4a6f))
* **gui:** add progress updates ([26e8b5f](https://github.com/AshKuhlmann/file_flow/commit/26e8b5f635ef769fa9bad24e4be30c1c9079d775))
* **gui:** add threaded queue-based progress ([083a2da](https://github.com/AshKuhlmann/file_flow/commit/083a2da935f81ab5386a1afcd704d67a1a08004e))
* **gui:** PyQt6 desktop shell wrapping CLI operations ([5483fc9](https://github.com/AshKuhlmann/file_flow/commit/5483fc9d0aef303af8cc7809cd6ac8ec012d0497))
* **mover:** add Mover class with dry-run ([5ebab20](https://github.com/AshKuhlmann/file_flow/commit/5ebab208694fa6df395dd1444184e76eff7b8851))
* **mover:** atomic moves with JSONL log & rollback ([e2cc41a](https://github.com/AshKuhlmann/file_flow/commit/e2cc41a9334c6aa37d342f9fa8b6ec4b0265e234))
* **rename:** allow custom patterns ([31c63b9](https://github.com/AshKuhlmann/file_flow/commit/31c63b9e7316f8868eb959dc8db75aa4b085603a))
* **renamer:** deterministic slug + collision-safe names ([f5db6d1](https://github.com/AshKuhlmann/file_flow/commit/f5db6d142070de28b1c2beb351aa5131934d18fb))
* **reporter:** generate styled Excel move report ([87a9e55](https://github.com/AshKuhlmann/file_flow/commit/87a9e552de073823e81fd6f65f8ad9723862c718))
* **review:** 30-day SQLite review queue engine ([4dc7cf2](https://github.com/AshKuhlmann/file_flow/commit/4dc7cf2708ab83c721744f7ac4ae07286fc19ede))
* **scanner:** recursive file discovery with hidden/symlink controls ([fceae93](https://github.com/AshKuhlmann/file_flow/commit/fceae93e55ca5170d04a6369cf16ff2e17a96255))
* **scheduler:** cross-platform nightly dry-run setup ([ecddf1f](https://github.com/AshKuhlmann/file_flow/commit/ecddf1f7939ce1f6195bd98bb31b56af2b14b5b7))
* **stats:** HTML dashboard for move-log analytics ([fbeca0c](https://github.com/AshKuhlmann/file_flow/commit/fbeca0c10e2bce6f0873b59d72bdbca4a9a9f728))
* **stats:** HTML dashboard for move-log analytics ([ee301a7](https://github.com/AshKuhlmann/file_flow/commit/ee301a75e56b928084ff04a2f00d410cd4aa62e9))


### Bug Fixes

* **build:** configure package discovery in pyproject.toml ([0329cac](https://github.com/AshKuhlmann/file_flow/commit/0329cac6e26ba94fe2ce265fb4e4cb8f8a18eaa1))
* **dev:** add pytest-cov to development dependencies ([9374c0e](https://github.com/AshKuhlmann/file_flow/commit/9374c0e1a17de8c8a7ef6dada64e9e7a7ee654e0))
* replace deprecated openpyxl font copy ([c683670](https://github.com/AshKuhlmann/file_flow/commit/c68367050209b48f3d5536ffaad9aef78d906d77))


### Documentation

* add feature summary and undo/review examples ([625d6b5](https://github.com/AshKuhlmann/file_flow/commit/625d6b5dca2b295b4823246ba8778d88159a94dd))
* add minimal config example ([6ad0d08](https://github.com/AshKuhlmann/file_flow/commit/6ad0d08f968dbfd42d828e047993c1fd36d57694))
* add quick start tutorial ([a7fa8a1](https://github.com/AshKuhlmann/file_flow/commit/a7fa8a1bfb54cd6deeef9b21d5ed1d292357ef1b))
* clarify install and CLI usage ([9410fe0](https://github.com/AshKuhlmann/file_flow/commit/9410fe017dc3464206684ebf3b49e77a018aab3c))
* consolidate changelog ([67305cd](https://github.com/AshKuhlmann/file_flow/commit/67305cd4d2cc4db89225b4943045047253f84d71))
* link to contributing in development section ([5d40052](https://github.com/AshKuhlmann/file_flow/commit/5d4005219b75034b32a81e8cb6fc091fef883514))
* MkDocs site, README demo, Pages workflow ([b44d1aa](https://github.com/AshKuhlmann/file_flow/commit/b44d1aa035c44c4245e0fd890f156552880639f5))
* remove GUI screenshot ([afe810d](https://github.com/AshKuhlmann/file_flow/commit/afe810d312f5574b3e509f51597812c238fe73fe))
* update CLI name references ([6444267](https://github.com/AshKuhlmann/file_flow/commit/6444267bb94a51b6c9462f80cc2f31e638ff511c))
* update setup instructions ([0c31b9d](https://github.com/AshKuhlmann/file_flow/commit/0c31b9ddef1f16b0d3e6350c9123c32a85183786))

## 1.0.0 – YYYY-MM-DD
* First stable release.
