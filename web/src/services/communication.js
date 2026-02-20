class CommunicationClient {
  #url;
  constructor(url) {
    this.#url = url;
  }

  async sendBarcode(barcode_value) {
    try {
      const response = await fetch(`${this.#url}?barcode=${barcode_value}`, {
        method: "POST",
        body: JSON.stringify({ barcode: barcode_value }),
      });
      if (!response.ok) {
        throw new Error(`Response status: ${response.status}`);
      }

      const json = await response.json();
    } catch (error) {
      alert(error);
      console.error(error.message);
    }
  }
}

export default CommunicationClient;
