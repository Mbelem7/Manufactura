document.addEventListener("DOMContentLoaded", () => {
    const addButton = document.getElementById("addComponentButton");
    const tableBody = document.getElementById("componentsTableBody");

    if (!addButton || !tableBody) {
        return;
    }

    const firstRow = tableBody.querySelector(".component-row");

    if (!firstRow) {
        return;
    }

    // La primera fila (que ya trae las opciones de componentes desde el servidor
    // y los nombres de campo del formulario) se guarda limpia como modelo.
    const rowTemplate = firstRow.cloneNode(true);

    rowTemplate.querySelectorAll("input:not([disabled])").forEach((input) => {
        input.value = "";
    });

    rowTemplate.querySelectorAll("select").forEach((select) => {
        select.selectedIndex = 0;
    });

    rowTemplate.querySelector(".component-unit").value = "-";


    addButton.addEventListener("click", () => {
        const row = rowTemplate.cloneNode(true);

        tableBody.appendChild(row);

        row.querySelector("select").focus();
    });


    // Al elegir un componente se muestra su unidad de medida
    tableBody.addEventListener("change", (event) => {
        const select = event.target.closest("select[name='producto_component_id']");

        if (!select) {
            return;
        }

        const row = select.closest(".component-row");
        const option = select.selectedOptions[0];

        row.querySelector(".component-unit").value =
            option && option.dataset.unidad ? option.dataset.unidad : "-";
    });


    tableBody.addEventListener("click", (event) => {
        const removeButton = event.target.closest(".remove-component");

        if (!removeButton) {
            return;
        }

        const rows = tableBody.querySelectorAll(".component-row");

        // Siempre debe quedar al menos una fila
        if (rows.length <= 1) {
            return;
        }

        removeButton.closest(".component-row").remove();
    });
});