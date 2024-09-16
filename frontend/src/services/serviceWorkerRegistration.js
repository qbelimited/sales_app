// src/serviceWorkerRegistration.js
import { register } from 'serviceWorkerRegistration';

register({
  onUpdate: registration => {
    if (window.confirm("New version available! Would you like to update?")) {
      registration.unregister().then(() => {
        window.location.reload();
      });
    }
  },
});
