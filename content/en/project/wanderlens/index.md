---
title: "WanderLens Travel Photos"
date: 2026-03-22
summary: "A cross-platform mobile app for capturing, organizing, and sharing travel photos with geolocation and trip timelines."
description: "A cross-platform mobile app for capturing, organizing, and sharing travel photos with geolocation and trip timelines."
tags: ["React Native", "Firebase", "TypeScript"]
github: "https://github.com/Bernard203/wanderLens"
---

WanderLens is a mobile application built with React Native and TypeScript that helps travelers document their journeys through photos. The app automatically organizes pictures by trip and location, plotting them on an interactive map so you can relive your routes. Firebase handles authentication, cloud storage for images, and real-time syncing across devices.

Each photo is geotagged on capture and enriched with reverse-geocoded place names. Users can create trip albums, add captions, and share selected highlights with friends via a unique link. The timeline view stitches photos together chronologically, letting users scroll through an entire trip day by day. Offline support ensures the app works in areas with limited connectivity -- photos are queued and uploaded when a connection is restored.

The design focuses on speed and simplicity. Images are compressed client-side before upload to minimize bandwidth usage, and thumbnails are generated via Firebase Cloud Functions for fast gallery loading. The project uses Expo for streamlined builds and over-the-air updates, making it easy to iterate quickly during development.
