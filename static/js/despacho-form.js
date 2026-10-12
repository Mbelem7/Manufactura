document.addEventListener("DOMContentLoaded", () => {
    const addButton = document.getElementById("addDispatchItemButton");
    const tableBody = document.getElementById("dispatchItemsTableBody");

    if (!addButton || !tableBody) {
        return;
    }

    const firstRow = tableBody.querySelector(".dispatch-item-row");

    if (!firstRow) {
        return;
    }

    // La primera fila (que ya trae las opciones de lote desde el servidor
    // y los nombres de campo del formulario) se guarda limpia como modelo.
    const rowTemplate = firstRow.cloneNode(true);

    rowTemplate.querySelectorAll("input").forEach((input) => {
        input.value = "";
    });

    rowTemplate.querySelectorAll("select").forEach((select) => {
        select.selectedIndex = 0;
    });


    // La cantidad no puede pasar de lo disponible en el lote elegido
    const adjustMax = (row) => {
        const select = row.querySelector("select[name='lote_id']");
        const quantityInput = row.querySelector("input[name='cantidad']");
        const option = select.selectedOptions[0];

        if (option && option.dataset.disponible) {
            quantityInput.max = option.dataset.disponible;
        } else {
            quantityInput.removeAttribute("max");
        }
    };

    tableBody.querySelectorAll(".dispatch-item-row").forEach(adjustMax);


    addButton.addEventListener("click", () => {
        const row = rowTemplate.cloneNode(true);

        tableBody.appendChild(row);

        row.querySelector("select").focus();
    });


    tableBody.addEventListener("change", (event) => {
        const select = event.target.closest("select[name='lote_id']");

        if (!select) {
            return;
        }

        adjustMax(select.closest(".dispatch-item-row"));
    });


    tableBody.addEventListener("click", (event) => {
        const removeButton = event.target.closest(".remove-dispatch-item");

        if (!removeButton) {
            return;
        }

        const rows = tableBody.querySelectorAll(".dispatch-item-row");

        // Siempre debe quedar al menos una fila
        if (rows.length <= 1) {
            return;
        }

        removeButton.closest(".dispatch-item-row").remove();
    });
});