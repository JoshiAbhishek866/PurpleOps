<template>
  <div id="app">
    <PageLoader />
    <Layout />
  </div>
</template>

<script setup>
import Layout from "@/components/Layout.vue";
import PageLoader from "@/components/PageLoader.vue";
</script>

<style>
/* ─── Font Declarations ────────────────────────────────────────────────────── */
@font-face {
  font-family: "Press Start 2P";
  src: url("/PressStart2P-Regular.ttf") format("truetype");
  font-weight: 400;
  font-style: normal;
  font-display: swap;
}

@font-face {
  font-family: "Ubuntu";
  src: url("/Ubuntu/Ubuntu-Light.ttf") format("truetype");
  font-weight: 300;
  font-style: normal;
  font-display: swap;
}
@font-face {
  font-family: "Ubuntu";
  src: url("/Ubuntu/Ubuntu-LightItalic.ttf") format("truetype");
  font-weight: 300;
  font-style: italic;
  font-display: swap;
}
@font-face {
  font-family: "Ubuntu";
  src: url("/Ubuntu/Ubuntu-Regular.ttf") format("truetype");
  font-weight: 400;
  font-style: normal;
  font-display: swap;
}
@font-face {
  font-family: "Ubuntu";
  src: url("/Ubuntu/Ubuntu-Italic.ttf") format("truetype");
  font-weight: 400;
  font-style: italic;
  font-display: swap;
}
@font-face {
  font-family: "Ubuntu";
  src: url("/Ubuntu/Ubuntu-Medium.ttf") format("truetype");
  font-weight: 500;
  font-style: normal;
  font-display: swap;
}
@font-face {
  font-family: "Ubuntu";
  src: url("/Ubuntu/Ubuntu-MediumItalic.ttf") format("truetype");
  font-weight: 500;
  font-style: italic;
  font-display: swap;
}
@font-face {
  font-family: "Ubuntu";
  src: url("/Ubuntu/Ubuntu-Bold.ttf") format("truetype");
  font-weight: 700;
  font-style: normal;
  font-display: swap;
}
@font-face {
  font-family: "Ubuntu";
  src: url("/Ubuntu/Ubuntu-BoldItalic.ttf") format("truetype");
  font-weight: 700;
  font-style: italic;
  font-display: swap;
}

/* ─── Design Tokens ─────────────────────────────────────────────────────────── */
:root {
  --font-heading: "Press Start 2P", monospace;
  --font-body: "Ubuntu", sans-serif;
}

/* ─── Global Reset ───────────────────────────────────────────────────────────── */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

/* ─── Base Typography ────────────────────────────────────────────────────────── */
body {
  font-family: var(--font-body);
  font-weight: 400;
  line-height: 1.7;
  transition: all 0.3s ease;
}

/* Headings use Press Start 2P */
h1,
h2,
h3,
h4 {
  font-family: var(--font-heading);
  line-height: 1.4;
  letter-spacing: -0.01em;
}

/* Paragraphs, labels, inputs, buttons — Ubuntu */
p,
span,
a,
li,
label,
input,
textarea,
select,
button,
td,
th {
  font-family: var(--font-body);
}

#app {
  background-color: #ffffff;
  color: #1a202c;
  min-height: 100vh;
}

/* ─── Scrollbar ──────────────────────────────────────────────────────────────── */
::-webkit-scrollbar {
  width: 6px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, #8b5cf6, #10b981);
  border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(135deg, #7c3aed, #059669);
}
</style>
