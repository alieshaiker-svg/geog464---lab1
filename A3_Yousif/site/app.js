const map = L.map('map', { preferCanvas: true });

const streets = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 19,
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);

const status = document.getElementById('status');
const boroughFilter = document.getElementById('borough-filter');
const rankingList = document.getElementById('ranking-list');
const rankingSummary = document.getElementById('ranking-summary');

function getDisplayValue(value) {
  if (value === null || value === undefined) {
    return '';
  }

  const text = String(value).trim();
  return text && text.toLowerCase() !== 'null' && text.toLowerCase() !== 'undefined'
    ? text
    : '';
}

function readStringProperty(properties, keys) {
  if (!properties) {
    return 'Unnamed playground';
  }

  for (let i = 0; i < keys.length; i += 1) {
    const value = getDisplayValue(properties[keys[i]]);
    if (value) {
      return value;
    }
  }

  return 'Unnamed playground';
}

function getCanopyPercent(feature) {
  const properties = feature && feature.properties ? feature.properties : {};
  const canopy = properties.canopy_pct_250m;
  return typeof canopy === 'number' && Number.isFinite(canopy) ? canopy : null;
}

function getPlaygroundId(feature) {
  const properties = feature && feature.properties ? feature.properties : {};
  return getDisplayValue(properties.ID);
}

function renderRankingList(visiblePlaygrounds, playgroundLayer, map) {
  rankingList.innerHTML = '';
  let highlightedMarker = null;

  if (!visiblePlaygrounds.length) {
    rankingSummary.textContent = 'No playgrounds match this borough.';
    return;
  }

  const rankedPlaygrounds = visiblePlaygrounds
    .map(function (feature) {
      const properties = feature.properties || {};
      const canopy = getCanopyPercent(feature);
      return {
        name: readStringProperty(properties, ['public_space_name']),
        category: [getDisplayValue(properties.NOM), getDisplayValue(properties.TYPE)]
          .filter(Boolean)
          .join(' / '),
        identifier: getPlaygroundId(feature),
        canopy: canopy
      };
    })
    .filter(function (playground) {
      return playground.canopy !== null;
    })
    .sort(function (a, b) {
      return b.canopy - a.canopy;
    })
    .slice(0, 10);

  if (!rankedPlaygrounds.length) {
    rankingSummary.textContent = 'No playgrounds with numeric canopy data in this borough.';
    return;
  }

  rankingSummary.textContent =
    'Top playgrounds ranked by tree canopy within 250 m. Showing ' +
    rankedPlaygrounds.length + ' of ' +
    visiblePlaygrounds.filter(function (feature) {
      return getCanopyPercent(feature) !== null;
    }).length + '.';

  rankedPlaygrounds.forEach(function (playground) {
    const item = document.createElement('li');
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'rank-select';
    button.addEventListener('click', function () {
      let marker = null;
      playgroundLayer.eachLayer(function (layer) {
        if (String(getPlaygroundId(layer.feature)) === playground.identifier) {
          marker = layer;
        }
      });

      if (!marker) {
        console.error('Could not find the selected playground marker on the map.');
        return;
      }

      if (highlightedMarker) {
        const previousCanopy = getCanopyPercent(highlightedMarker.feature);
        highlightedMarker.setStyle({
          radius: 5,
          color: '#ffffff',
          weight: 1,
          fillOpacity: 0.95,
          fillColor: previousCanopy === null ? '#777777' : colourForCanopy(previousCanopy)
        });
      }

      marker.setStyle({
        radius: 9,
        color: '#1F2D5A',
        weight: 3,
        fillColor: '#ffffff',
        fillOpacity: 1
      });
      marker.bringToFront();
      map.flyTo(marker.getLatLng(), Math.max(map.getZoom(), 16));
      marker.openPopup();
      highlightedMarker = marker;
    });

    const name = document.createElement('strong');
    name.textContent = playground.name;
    button.appendChild(name);

    if (playground.category) {
      const category = document.createElement('span');
      category.className = 'rank-identifier';
      category.textContent = playground.category;
      button.appendChild(category);
    }

    const meta = document.createElement('span');
    meta.className = 'rank-meta';
    meta.textContent = 'Tree canopy within 250 m: ' + playground.canopy.toFixed(1) + '%';
    button.appendChild(meta);

    if (playground.identifier) {
      const identifier = document.createElement('span');
      identifier.className = 'rank-identifier';
      identifier.textContent = 'ID ' + String(playground.identifier);
      button.appendChild(identifier);
    }

    item.appendChild(button);
    rankingList.appendChild(item);
  });
}

function loadGeoJSON(path) {
  return fetch(path).then(function (response) {
    if (!response.ok) {
      throw new Error('HTTP ' + response.status + ' loading ' + path);
    }
    return response.json();
  }).then(function (data) {
    if (!Array.isArray(data.features)) {
      throw new Error(path + ' does not contain a GeoJSON features array');
    }
    return data;
  });
}

function colourForCanopy(value) {
  if (value === 0) { return '#f7fcf5'; }
  if (value < 10) { return '#e5f5e0'; }
  if (value < 20) { return '#a1d99b'; }
  if (value < 40) { return '#31a354'; }
  return '#006d2c';
}

Promise.all([
  loadGeoJSON('../data/playgrounds_public_access.geojson'),
  loadGeoJSON('../data/canopy_grid.geojson')
])
  .then(function (datasets) {
    const playgroundData = datasets[0];
    const canopyGridData = datasets[1];
    const playgrounds = playgroundData.features.filter(function (feature) {
      return feature.properties &&
        feature.properties.access_class === 'municipal_public_space';
    });
    if (playgrounds.length !== 918) {
      throw new Error('playgrounds_public_access.geojson must contain exactly 918 municipal playgrounds');
    }
    const boroughs = Array.from(new Set(playgrounds.map(function (feature) {
      return feature.properties.ARROND;
    }).filter(Boolean))).sort();

    boroughs.forEach(function (borough) {
      const option = document.createElement('option');
      option.value = borough;
      option.textContent = borough;
      boroughFilter.appendChild(option);
    });

    map.createPane('canopyGridPane');
    map.getPane('canopyGridPane').style.zIndex = 350;

    const canopyGridLayer = L.geoJSON(canopyGridData, {
      pane: 'canopyGridPane',
      style: function (feature) {
        return {
          color: '#385442',
          weight: 0.45,
          opacity: 0.55,
          fillColor: colourForCanopy(feature.properties.canopy_pct),
          fillOpacity: 0.42
        };
      },
      onEachFeature: function (feature, layer) {
        layer.bindPopup(
          'Tree canopy in this 1 km square: ' +
          Number(feature.properties.canopy_pct).toFixed(1) + '%'
        );
      }
    }).addTo(map);

    const playgroundLayer = L.geoJSON([], {
      pointToLayer: function (feature, latlng) {
        const canopy = getCanopyPercent(feature);
        return L.circleMarker(latlng, {
          radius: 5,
          color: '#ffffff',
          weight: 1,
          fillOpacity: 0.95,
          fillColor: canopy === null ? '#777777' : colourForCanopy(canopy)
        });
      },
      onEachFeature: function (feature, layer) {
        const p = feature.properties;
        const canopy = getCanopyPercent(feature);
        const popup = document.createElement('div');
        const heading = document.createElement('h3');
        heading.textContent = readStringProperty(p, ['public_space_name']);
        popup.appendChild(heading);

        [
          ['Age/category', p.NOM],
          ['Type', p.TYPE],
          ['Borough', p.ARROND],
          ['Tree canopy within 250 m', canopy === null ? '' : canopy.toFixed(1) + '%'],
          ['Playground ID', getPlaygroundId(feature)]
        ].forEach(function (item) {
          const value = getDisplayValue(item[1]);
          if (!value) {
            return;
          }
          const line = document.createElement('div');
          line.textContent = item[0] + ': ' + value;
          popup.appendChild(line);
        });

        layer.bindPopup(popup);
      }
    }).addTo(map);

    const overlayLayers = {
      'Playground locations': playgroundLayer,
      'Tree canopy (2019)': canopyGridLayer
    };
    L.control.layers({ 'OpenStreetMap': streets }, overlayLayers, {
      collapsed: false
    }).addTo(map);

    const legend = L.control({ position: 'bottomright' });
    legend.onAdd = function () {
      const div = L.DomUtil.create('div', 'legend');
      const title = L.DomUtil.create('div', 'legend-title', div);
      title.textContent = 'Tree canopy coverage per 1 km square (%)';

      [
        { label: '0%', value: 0 },
        { label: '>0–<10%', value: 5 },
        { label: '10–<20%', value: 15 },
        { label: '20–<40%', value: 30 },
        { label: '40%+', value: 40 }
      ].forEach(function (range) {
        const row = L.DomUtil.create('div', 'legend-row', div);
        const swatch = L.DomUtil.create('span', 'legend-swatch', row);
        swatch.style.backgroundColor = colourForCanopy(range.value);
        const label = L.DomUtil.create('span', '', row);
        label.textContent = range.label;
      });

      return div;
    };
    legend.addTo(map);

    function updateMap() {
      const selectedBorough = boroughFilter.value;
      const visiblePlaygrounds = playgrounds.filter(function (feature) {
        return !selectedBorough || feature.properties.ARROND === selectedBorough;
      });

      const openPopups = [];
      map.eachLayer(function (layer) {
        if (layer instanceof L.Popup) {
          openPopups.push(layer);
        }
      });
      openPopups.forEach(function (popup) {
        map.closePopup(popup);
      });
      playgroundLayer.clearLayers();
      playgroundLayer.addData(visiblePlaygrounds);
      status.textContent = selectedBorough
        ? visiblePlaygrounds.length + ' playgrounds shown in ' + selectedBorough
        : visiblePlaygrounds.length + ' playgrounds shown across Montreal';
      renderRankingList(visiblePlaygrounds, playgroundLayer, map);

      if (visiblePlaygrounds.length > 0) {
        map.fitBounds(playgroundLayer.getBounds(), { padding: [20, 20] });
      } else {
        map.setView([45.5019, -73.5674], 11);
      }
    }

    function showPlayground(feature) {
      const id = String(feature.properties.ID);
      boroughFilter.value = feature.properties.ARROND || '';
      updateMap();

      let marker = null;
      playgroundLayer.eachLayer(function (layer) {
        const properties = layer.feature && layer.feature.properties;
        if (properties && String(properties.ID) === id) {
          marker = layer;
        }
      });

      if (!marker) {
        console.error('Could not find the saved playground marker on the map.');
        return;
      }

      map.flyTo(marker.getLatLng(), Math.max(map.getZoom(), 15));
      marker.openPopup();
    }

    boroughFilter.disabled = false;
    boroughFilter.addEventListener('change', updateMap);
    updateMap();
    rememberMarks(map, playgroundLayer, {
      idField: 'ID',
      nameField: 'public_space_name',
      title: 'My playgrounds',
      onSelect: showPlayground
    });
  })
  .catch(function (err) {
    status.textContent =
      'Could not load map data. Open the console (F12) for details.';
    console.error(err);
  });
