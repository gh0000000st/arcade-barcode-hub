import CommunicationClient from "../../services/communication.js";
import StorageHandler from "../../services/storage-handler.js";
import css from "./card.css?raw";
import html from "./card.html?raw";
import CardHeader from "../card-header/card-header.js";
import Options from "../options/options.js";
import MenuButton from "../menu-button/menu-button.js";
const ipAdressKeyName = "ipAdress";

class CardComponent extends HTMLElement {
  #client;
  #addCollectionButton;
  #storageHandler;

  static observedAttributes = ["istoggled"];
  constructor() {
    super();
    this._shadow = this.attachShadow({ mode: "open" });
    this.storageHandler = new StorageHandler();
    this.getCommunicationClient();
  }

  getCommunicationClient() {
    this.#client = new CommunicationClient(
      `http://${this.storageHandler.getDataFromLocalStorage(ipAdressKeyName)}/api/barcode`,
    );
  }

  setData(dino) {
    this._data = dino;
  }

  connectedCallback() {
    this.#storageHandler = new StorageHandler();
    this._shadow.innerHTML = `<style>${css}</style>${html}`;
    if (this._data) {
      this.render();
    }
    this.#addCollectionButton = this._shadow.getElementById("addCollection");

    this.#addCollectionButton.addEventListener("click", (e) => {
      this.dispatchEvent(
        new CustomEvent("added-to-collection", {
          detail: { value: this._data },
          bubbles: true,
          composed: true,
        }),
      );
      this.dispatchEvent(
        new CustomEvent("filter-changed", {
          bubbles: true,
          composed: true,
        }),
      );
    });
  }
  sendCode = () => {
    this.#client.sendBarcode(this._data.card_code);
  };

  render() {
    if (!this._data) return;
    console.log(this._data);
    const dino = this._data;
    const card = this._shadow.querySelector("#card");
    const existingStats = this.querySelector('[slot="stats"]');

    card.addEventListener("click", this.sendCode);
    if (existingStats) existingStats.remove();

    if (this._data.stats?.attack) {
      const statsHeader = document.createElement("card-header");
      statsHeader.setAttribute("slot", "stats");
      statsHeader.setData(this._data.stats);
      this.appendChild(statsHeader);
    }

    if (dino.card_type?.toLowerCase() === "move") {
      //  card.classList.add("move");
      console.log(dino.stats?.sign[0].toLowerCase());
      this._shadow
        .querySelectorAll("span.attack.stat")
        .forEach((el) =>
          el.querySelector("p").id != dino.stats?.sign[0].toLowerCase()
            ? el.remove()
            : "",
        );
    }

    this._shadow.getElementById("name").textContent = dino.name;
    this._shadow.getElementById("game").textContent =
      dino.compat != "" ? dino.compat : "N/A";
    this._shadow.getElementById("type").textContent = dino.type;
    if (dino.card_type?.toLowerCase() != "move") {
      this._shadow.getElementById("rock").textContent =
        dino.stats.attack != undefined ? dino.stats.attack.Rock : 0;
      this._shadow.getElementById("paper").textContent =
        dino.stats.attack != undefined ? dino.stats.attack.Paper : 0;
      this._shadow.getElementById("scissors").textContent =
        dino.stats.attack != undefined ? dino.stats.attack.Scissors : 0;
    }
    card.classList.add(dino.sign);
    if (dino.cardCode && dino.cardCode !== "undefined") {
      // card.classList.add(dino.cardCode);
    } else {
      card.classList.add("empty-card-code");
    }
  }
}

customElements.define("card-component", CardComponent);
