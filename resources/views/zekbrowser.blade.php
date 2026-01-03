<!DOCTYPE html>
<html lang="{{ str_replace('_', '-', app()->getLocale()) }}">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        
        <script>
            (function() 
            {
                const appearance = '{{ $appearance ?? "light" }}';
                const root = document.documentElement;

                window.__INITIAL_APPEARANCE__ = appearance;
                
                if (appearance === 'dark') 
                {
                    root.classList.add('dark');
                    root.setAttribute('data-theme', 'dark');
                } 
                else 
                {
                    root.classList.remove('dark');
                    root.setAttribute('data-theme', 'light');
                }
            })();
        </script>

        <title inertia>{{ config('app.name', 'ElDewrito Services') }}</title>

        <link rel="icon" type="image/png" href="/favicon-96x96.png" sizes="96x96" />
        <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
        <link rel="shortcut icon" href="/favicon.ico" />
        <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png" />
        <meta name="apple-mobile-web-app-title" content="ED Services" />
        <link rel="manifest" href="/site.webmanifest" />

        @routes
        @vite(['resources/js/app.ts', "resources/js/pages/{$page['component']}.vue"])
        @inertiaHead
    </head>
    <body class="font-sans antialiased">
        @inertia
    </body>
</html>
