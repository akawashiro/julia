# メモ

Ruby の JIT での高速化は 2~3倍程度である。
[https://speed.yjit.org/](https://speed.yjit.org/)

一方 Julia は JIT で64倍程度高速化されている。
これはインタプリタの実装が悪そう。
```
$ ../julia --version
julia version 1.11.2
$ hyperfine '../julia nbody.jl 1> /dev/null'
Benchmark 1: ../julia nbody.jl 1> /dev/null
  Time (mean ± σ):      1.510 s ±  0.143 s    [User: 1.476 s, System: 0.140 s]
  Range (min … max):    1.375 s …  1.873 s    10 runs
$ hyperfine '../julia --compile=no --compiled-modules=no nbody.jl 1> /dev/null'
Benchmark 1: ../julia --compile=no --compiled-modules=no nbody.jl 1> /dev/null
  Time (mean ± σ):     98.725 s ± 19.581 s    [User: 98.403 s, System: 0.314 s]
  Range (min … max):   78.084 s … 133.442 s    10 runs
```

```
$ sudo ./nbody_profile.sh
$ sudo perf report --input nbody_compile_no.profile --no-children -Mintel
```

`jl_is_gotonode(stmt)` とかが遅い

https://github.com/JuliaLang/julia/issues/1064

https://www.google.com/url?sa=t&source=web&rct=j&opi=89978449&url=https://ipsj.ixsq.nii.ac.jp/ej/%3Faction%3Drepository_action_common_download%26item_id%3D16575%26item_no%3D1%26attribute_id%3D1%26file_no%3D1&ved=2ahUKEwiRm77lx9GKAxWJrlYBHQgPOygQFnoECD0QAQ&usg=AOvVaw2DXt1pR5HQqncAHvZrPHP5

https://www.abap34.com/posts/jci_00.html
