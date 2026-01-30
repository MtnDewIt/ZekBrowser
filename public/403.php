<?php
// Simple PHP 403 page that picks a random image from public/assets/404 if available
$imgDir = __DIR__ . '/assets/404';
$images = [];
if (is_dir($imgDir)) {
    $files = scandir($imgDir);
    foreach ($files as $f) {
        $ext = strtolower(pathinfo($f, PATHINFO_EXTENSION));
        if (in_array($ext, ['jpg','jpeg','png','webp','gif'])) {
            $images[] = '/assets/404/' . rawurlencode($f);
        }
    }
}
$bg = count($images) ? $images[array_rand($images)] : null;
if ($bg) {
    $bg .= (strpos($bg, '?') === false ? '?' : '&') . 'cb=' . time();
}
http_response_code(403);
?>
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>403 — Forbidden</title>
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
<?php if ($bg): ?>
  <div class="bg" style="background-image:url('<?php echo htmlspecialchars($bg, ENT_QUOTES); ?>')"></div>
<?php else: ?>
  <div class="bg" style="background:linear-gradient(180deg,#0b0b0b,#1a1a1a)"></div>
<?php endif; ?>

  <div class="overlay">
    <h1>403 — Forbidden</h1>
    <p>Sorry, you don't have permission to access this page.</p>
    <a class="btn" href="/">Go home</a>
  </div>
</body>
</html>
