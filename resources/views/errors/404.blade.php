<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Page Not Found</title>
  <style>
    html,body{height:100%;margin:0}
    body{display:flex;align-items:center;justify-content:center;font-family:Inter,system-ui,Segoe UI,Roboto,"Helvetica Neue",Arial;color:#fff}
    .bg{position:fixed;inset:0;background-color:#111;background-size:cover;background-position:center;filter:brightness(.6)}
    .overlay{position:relative;z-index:2;text-align:center;padding:2rem}
    h1{font-size:3rem;margin:0 0 .5rem}
    p{margin:.5rem 0 1.25rem;color:rgba(255,255,255,.85)}
    a.btn{display:inline-block;padding:.6rem 1.1rem;border-radius:.5rem;background:rgba(255,255,255,.12);color:#fff;text-decoration:none;border:1px solid rgba(255,255,255,.08)}
    @media (prefers-color-scheme:dark){
      body{color:#fff}
      a.btn{background:rgba(255,255,255,.06)}
    }
  </style>
</head>
<body>
@php
    $imgDir = public_path('assets/404');
    $images = [];
    if (file_exists($imgDir) && is_dir($imgDir)) {
        foreach (scandir($imgDir) as $f) {
                if (in_array(strtolower(pathinfo($f, PATHINFO_EXTENSION)), ['jpg','jpeg','png','webp','gif'])) {
                $images[] = asset('assets/404/'.$f);
            }
        }
    }
    $bg = count($images) ? $images[array_rand($images)] : null;
    if ($bg) {
      $bg .= (strpos($bg, '?') === false ? '?' : '&') . 'cb=' . time();
    }
@endphp

@if($bg)
  <div class="bg" style="background-image:url('{{ $bg }}')"></div>
@else
  <div class="bg" style="background:linear-gradient(180deg,#0b0b0b,#1a1a1a)"></div>
@endif

  <div class="overlay">
    <h1>404 — Page Not Found</h1>
    <p>Sorry, we couldn't find that page.</p>
    <a class="btn" href="{{ url('/') }}">Go home</a>
  </div>
</body>
</html>
