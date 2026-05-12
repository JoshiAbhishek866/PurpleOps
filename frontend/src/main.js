import { createApp } from "vue";
import { createPinia } from "pinia";
import { createHead } from "@vueuse/head";
import router from "./router";
import App from "./App.vue";
import "./style.css";

// Always start at the top on page load / refresh
if ("scrollRestoration" in history) {
  history.scrollRestoration = "manual";
}
window.scrollTo(0, 0);

const app = createApp(App);
const head = createHead();

app.use(createPinia());
app.use(router);
app.use(head);

app.mount("#app");
