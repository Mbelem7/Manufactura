document.addEventListener("DOMContentLoaded", () => {
    const addButton = document.getElementById("addComponentButton");
    const tableBody = document.getElementById("componentsTableBody");

    if (!addButton || !tableBody) {
        return;
    }

    const createComponentRow = () => {
        const row = document.createElement("tr");

        row.classList.add("component-row");

        row.innerHTML = `
            <td>
                <select
                    name="producto_component_id[]"
                    class="form-select"
                    required
                >
                    <option value="">
                        Seleccione un componente
                    </option>
                </select>
            </td>

            <td>
                <input
                    type="number"
                    name="cantidad[]"
                    class="form-control"
                    min="0.01"
                    step="0.01"
                    placeholder="0.00"
                    required
                >
            </td>

            <td>
                <input
                    type="text"
                    class="form-control"
                    value="-"
                    disabled
                >
            </td>

            <td class="text-end">
                <button
                    type="button"
                    class="btn btn-outline-danger btn-sm remove-component"
                    title="Eliminar componente"
                >
                    <i class="bi bi-trash"></i>
                </button>
            </td>
        `;

        return row;
    };

    addButton.addEventListener("click", () => {
        tableBody.appendChild(createComponentRow());
    });

    tableBody.addEventListener("click", (event) => {
        const removeButton = event.target.closest(".remove-component");

        if (!removeButton) {
            return;
        }

        const rows = tableBody.querySelectorAll(".component-row");

        if (rows.length <= 1) {
            return;
        }

        removeButton.closest(".component-row").remove();
    });
});