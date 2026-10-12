document.addEventListener("DOMContentLoaded", () => {
    const addButton = document.getElementById("addReceptionItemButton");
    const tableBody = document.getElementById("receptionItemsTableBody");

    if (!addButton || !tableBody) {
        return;
    }

    const firstRow = tableBody.querySelector(".reception-item-row");

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


    tableBody.addEventListener("click", (event) => {
        const removeButton = event.target.closest(".remove-reception-item");

        if (!removeButton) {
            return;
        }

        const rows = tableBody.querySelectorAll(".reception-item-row");

        // Siempre debe quedar al menos una fila
        if (rows.length <= 1) {
            return;
        }

        removeButton.closest(".reception-item-row").remove();
    });
});