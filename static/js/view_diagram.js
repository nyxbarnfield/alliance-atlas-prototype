document.addEventListener("DOMContentLoaded", function () {
  const filters = {
    faction: "",
    species: "",
    occupation: "",
    search: ""
  };

  // ----- Plugin Registration -----
  function registerLayoutPlugin() {
    try {
      if (window.cytoscape && window.cytoscapeCoseBilkent) {
        cytoscape.use(window.cytoscapeCoseBilkent);
        console.log("✅ cose-bilkent registered");
      } else {
        console.warn("⚠️ cose-bilkent not available");
      }
    } catch (e) {
      console.error("❌ Error registering cose-bilkent:", e);
    }
  }

  // ----- Cytoscape Setup -----
  function createCyInstance(elements) {
    return cytoscape({
      container: document.getElementById('cy'),
      elements,
      style: getCyStyle(),
      maxZoom: 2,
      minZoom: 0.5,
      motionBlur: true,
      autoungrabify: false,
      boxSelectionEnabled: false
    });
  }

  function getCyStyle() {
    return [
      {
        selector: 'node',
        style: {
          'label': 'data(label)',
          'background-color': 'data(color)',
          'text-valign': 'center',
          'text-halign': 'center',
          'color': '#fff',
          'font-size': '12px',
          'text-wrap': 'wrap',
          'text-max-width': 80,
          'text-outline-width': 2,
          'text-outline-color': '#333',
          'font-family': 'Arial, sans-serif'
        }
      },
      {
        selector: 'node:parent',
        style: {
          'label': 'data(label)',
          'background-color': '#f8f9fa',
          'border-width': 2,
          'border-color': '#666',
          'text-valign': 'top',
          'text-halign': 'center',
          'font-size': '13px',
          'font-weight': '500',
          'color': '#333',
          'shape': 'roundrectangle',
          'padding': '30px',
          'min-width': '200px',
          'min-height': '100px',
          'text-margin-y': '-5px',
          'font-family': 'Arial, sans-serif',
          'text-outline-width': 0
        }
      },
      {
        selector: 'edge',
        style: {
          'width': 3,
          'line-color': 'data(color)',
          'target-arrow-color': 'data(color)',
          'target-arrow-shape': 'triangle',
          'curve-style': 'bezier'
        }
      }
    ];
  }

  function runLayout(cyInstance) {
    const layout = cyInstance.layout({
      name: 'cose-bilkent',
      animate: true,
      fit: true,
      padding: 60,
      nodeRepulsion: 12000,
      idealEdgeLength: 80,
      edgeElasticity: 0.4,
      nestingFactor: 1.1,
      gravity: 0.9,
      gravityRange: 3.0,
      gravityCompound: 1.4,
      nodeSpacing: 30,
      avoidOverlap: true,
      nodeDimensionsIncludeLabels: true,
      tile: true,
      randomize: false,
      numIter: 3000
    });

    layout.run();
    setTimeout(() => cyInstance.fit(cyInstance.nodes(), 40), 1000);
  }

  // ----- UI Dropdowns -----
  function populateDropdowns(cyInstance) {
    const characterNodes = cyInstance.nodes().filter(n => ['PC', 'NPC'].includes(n.data('type')));
    const getUniqueValues = field =>
      [...new Set(characterNodes.map(n => n.data(field)).filter(Boolean))];

    const setOptions = (id, values) => {
      const select = document.getElementById(id);
      if (!select) return;
      select.innerHTML = '<option value="">All</option>';
      values.sort().forEach(val => {
        const opt = document.createElement("option");
        opt.value = val;
        opt.textContent = val;
        select.appendChild(opt);
      });
    };

    setOptions("factionFilter", getUniqueValues("faction"));
    setOptions("speciesFilter", getUniqueValues("species"));
    setOptions("occupationFilter", getUniqueValues("occupation"));
  }

  // ----- Filter Logic -----
  function applyFilters(cyInstance) {
    const chipsContainer = document.getElementById("activeFilters");
    chipsContainer.innerHTML = "";

    Object.entries(filters).forEach(([key, value]) => {
      if (!value) return;
      const chip = document.createElement("span");
      chip.className = "badge bg-primary";
      chip.innerHTML = `${key}: ${value} <button class="btn-close btn-close-white btn-sm ms-2" aria-label="Close"></button>`;
      chip.querySelector("button").onclick = () => {
        filters[key] = "";
        if (key === "search") {
          document.getElementById("searchInput").value = "";
        } else {
          document.getElementById(`${key}Filter`).value = "";
        }
        applyFilters(cyInstance);
      };
      chipsContainer.appendChild(chip);
    });

    cyInstance.nodes().forEach(node => {
      const data = node.data();
      const isGroup = !data.parent;

      if (isGroup) {
        node.style("display", "element");
        return;
      }

      const match =
        (!filters.faction || data.faction === filters.faction) &&
        (!filters.species || data.species === filters.species) &&
        (!filters.occupation || data.occupation === filters.occupation) &&
        (!filters.search || data.label?.toLowerCase().includes(filters.search.toLowerCase()));

      node.style("display", match ? "element" : "none");
    });

    cyInstance.edges().forEach(edge => {
      const sourceVisible = edge.source().style("display") === "element";
      const targetVisible = edge.target().style("display") === "element";
      edge.style("display", sourceVisible && targetVisible ? "element" : "none");
    });

    const visibleNodes = cyInstance.nodes().filter(n => n.style("display") === "element" && n.data("parent"));
    if (visibleNodes.length > 0) {
      cyInstance.fit(visibleNodes, 50);
    }

    document.getElementById("visibleCount").innerText = `${visibleNodes.length} characters visible`;
  }

  function setupFilters(cyInstance) {
    ["faction", "species", "occupation"].forEach(type => {
      const input = document.getElementById(`${type}Filter`);
      if (input) {
        input.addEventListener("change", e => {
          filters[type] = e.target.value;
          applyFilters(cyInstance);
        });
      }
    });

    const searchInput = document.getElementById("searchInput");
    if (searchInput) {
      searchInput.addEventListener("input", e => {
        filters.search = e.target.value;
        applyFilters(cyInstance);
      });
    }

    const clearBtn = document.getElementById("clearFilters");
    if (clearBtn) {
      clearBtn.addEventListener("click", () => {
        Object.keys(filters).forEach(key => {
          filters[key] = "";
          const el = document.getElementById(`${key}Filter`) || document.getElementById("searchInput");
          if (el) el.value = "";
        });
        applyFilters(cyInstance);
      });
    }
  }

  // ----- Modal -----
  function setupModal(cyInstance) {
    cyInstance.on('tap', 'node', function (evt) {
      const data = evt.target.data();
      if (!data.species && !data.occupation && !data.age_range && !data.description) return;

      const html = `
        <strong>${data.label}</strong><br>
        <small><strong>Species:</strong> ${data.species || 'Unknown'}</small><br>
        <small><strong>Occupation:</strong> ${data.occupation || 'Unknown'}</small><br>
        <small><strong>Age Range:</strong> ${data.age_range || 'Unknown'}</small><br>
        ${data.description ? `<small><strong>Description:</strong> ${data.description}</small>` : ''}
      `;
      document.getElementById('characterModalBody').innerHTML = html;
      new bootstrap.Modal(document.getElementById('characterModal')).show();
    });
  }

  // ----- Init -----
  registerLayoutPlugin();
  const cyInstance = createCyInstance(window.campaignElements || []);
  runLayout(cyInstance);
  populateDropdowns(cyInstance);
  setupFilters(cyInstance);
  setupModal(cyInstance);

  const resetButton = document.getElementById('resetView');
  if (resetButton) {
    resetButton.addEventListener('click', () => cyInstance.fit());
  }
});
