document.addEventListener("DOMContentLoaded", () => {
    const addButton = document.getElementById("addSaleItemButton");
    const tableBody = document.getElementById("saleItemsTableBody");

    if (!addButton || !tableBody) {
        return;
    }

    const firstRow = tableBody.querySelector(".sale-item-row");

    if (!firstRow) {
        return;
    }

    // La primera fila (que ya trae las opciones de producto desde el servidor
    // y los nombres de campo del formulario) se guarda limpia como modelo.
    const rowTemplate = firstRow.cloneNode(true);

    rowTemplate.querySelectorAll("input").forEach((input) => {
        input.value = "";
    });

    rowTemplate.querySelectorAll("select").forEach((select) => {
        select.selectedIndex = 0;
    });


    addButton.addEventListener("click", () => {
        const row = rowTemplate.cloneNode(true);

        tableBody.appendChild(row);

        row.querySelector("select").focus();
    });


    // Al elegir un producto se sugiere su precio de venta
    tableBody.addEventListener("change", (event) => {
        const select = event.target.closest("select[name='producto_id']");

        if (!select) {
            return;
        }

        const row = select.closest(".sale-item-row");
        const priceInput = row.querySelector("input[name='precio_unitario']");
        const option = select.selectedOptions[0];

        if (priceInput) {
            priceInput.value = option && option.dataset.precio ? option.dataset.precio : "";
        }
    });


    tableBody.addEventListener("click", (event) => {
        const removeButton = event.target.closest(".remove-sale-item");

        if (!removeButton) {
            return;
        }

        const rows = tableBody.querySelectorAll(".sale-item-row");

        // Siempre debe quedar al menos una fila
        if (rows.length <= 1) {
            return;
        }

        removeButton.closest(".sale-item-row").remove();
    });
});