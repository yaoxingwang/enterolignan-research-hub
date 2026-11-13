const filter = document.querySelector("[data-filter]");
if (filter) {
  const buttons = Array.from(filter.querySelectorAll("button"));
  const rows = Array.from(document.querySelectorAll("[data-status]"));
  const count = document.querySelector("[data-filter-count]");
  for (const button of buttons) {
    button.addEventListener("click", () => {
      const value = button.dataset.filterValue;
      for (const candidate of buttons) {
        candidate.setAttribute("aria-pressed", String(candidate === button));
      }
      for (const row of rows) {
        row.hidden = value !== "all" && row.dataset.status !== value;
      }
      count.textContent = `显示 ${rows.filter((row) => !row.hidden).length} 个数据模块`;
    });
  }
}

const weight = document.querySelector("#example-weight");
if (weight) {
  const displayedWeight = document.querySelector("#example-weight-value");
  const result = document.querySelector("#weighted-mean");
  weight.addEventListener("input", () => {
    const secondWeight = Number(weight.value);
    displayedWeight.value = String(secondWeight);
    result.value = ((60 * 100 + 100 * secondWeight) / (100 + secondWeight)).toFixed(1);
  });
}
