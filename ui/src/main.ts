import { mount } from 'svelte';
import App from './App.svelte';
import './design/global.css';

const app = mount(App, {
  target: document.getElementById('app')!,
});

export default app;
