# ZekBrowser

[![Docker Image](https://img.shields.io/badge/docker-latest-blue.svg)](https://github.com/MtnDewIt/ZekBrowser)

A modern, open-source server browser and API for ElDewrito, Project Cartographer, Halo Custom Edition and The Master Chief Collection, built with Laravel, Vue 3, and FastAPI. Provides real-time server listings, player statistics, historical data tracking all in a clean and flexible interface.

## Source Code

Full source code available at: **[https://github.com/MtnDewIt/ZekBrowser](https://github.com/MtnDewIt/ZekBrowser)**

## Support

For issues, questions, or contributions, please visit the [GitHub repository](https://github.com/MtnDewIt/ZekBrowser).

## Credits

This project is based on the original work by **pauwlo** — see
[ElDewrito-Services](https://github.com/Pauwlo/ElDewrito-Services).

## Unraid Configuration

To ensure your database persists across updates in Unraid, you **must** configure a Path mapping:

1.  **Container Path**: `/var/www/database`
2.  **Host Path**: direct to a share, e.g., `/mnt/user/appdata/zekbrowser/database/`

&nbsp;

**Note**: If you have an existing `database.sqlite` file (e.g. from a backup) that you wish to import into the new volume, you can mount the folder containing it to `/legacy_database_import` (Container Path) for the first startup. The system will copy it into the proper location automatically.