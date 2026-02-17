import "./components/card/card.js";
import "./components/sidebar/sidebar.js";
import "./components/modal/modal.js";
import "./components/filter/filter.js";
import DataHandler from "./services/data-handler.js";
import "./components/collection/collection.js";
import StorageHandler from "./services/storage-handler.js";
import * as init from "./services/init.js";
import { createFilter, initFilter } from "./services/init.js";
import "./components/filter-list/filter-list.js";
let dinos;
let dataHandler;
let filterIndex = 0;
const storageHandler = new StorageHandler();
document.addEventListener("DOMContentLoaded", async () => {
  await init.init();

  document.addEventListener("active-filter", (e) => {
    filterIndex = e.detail.value;
    document
      .getElementsByTagName("filter-component")[0]
      .setAttribute("filter_index", filterIndex);
  });
  document.addEventListener("added-to-collection", (e) => {
    let storage = JSON.parse(
      storageHandler.getDataFromLocalStorage(`dino-collection-${filterIndex}`),
    );
    if (!storage) {
      storage = [];
    }
    const newValue = e.detail.value;
    const itemIndex = storage.findIndex((item) => item.id === newValue.id);
    if (itemIndex > -1) {
      storage.splice(itemIndex, 1);
    } else {
      storage.push(newValue);
    }
    storageHandler.setDataFromLocalStorage(
      `dino-collection-${filterIndex}`,
      JSON.stringify(storage),
    );
  });
});
