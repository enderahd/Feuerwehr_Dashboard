const pdfUrls = [
  'pdfs/1.pdf',
  'pdfs/2.pdf',
  'pdfs/3.pdf',
  'pdfs/4.pdf',
  'pdfs/5.pdf',
  'pdfs/6.pdf'
];

const intervalTimes = [15000, 15000, 15000, 15000, 15000, 15000];
const reloadInterval = 60000; // 1 Minute in Millisekunden
const totalPdfs = pdfUrls.length;
const canvases = document.querySelectorAll('.pdf-container canvas');
let currentPages = new Array(totalPdfs).fill(1);
let pdfDocuments = [];
let renderTasks = new Array(totalPdfs).fill(null);

// Funktion zum Laden der PDFs
function loadPdfs() {
  pdfDocuments = []; // Leere das Array, um alte Referenzen zu entfernen
  pdfUrls.forEach((url, index) => {
    pdfjsLib.getDocument(url).promise.then(function (pdfDoc) {
      pdfDocuments[index] = pdfDoc;
      displayPage(index, currentPages[index]);
    }).catch(error => {
      console.error(`Fehler beim Laden der PDF ${url}:`, error);
    });
  });
}

// Funktion zum Anzeigen einer Seite
function displayPage(pdfIndex, pageNum) {
  const canvas = canvases[pdfIndex];
  const context = canvas.getContext('2d');

  if (renderTasks[pdfIndex]) {
    renderTasks[pdfIndex].cancel();
    renderTasks[pdfIndex] = null;
  }

  pdfDocuments[pdfIndex].getPage(pageNum).then(function (page) {
    const viewport = page.getViewport({ scale: 1.5 });

    const containerWidth = canvas.parentElement.clientWidth;
    const containerHeight = canvas.parentElement.clientHeight;
    const scale = Math.min(containerWidth / viewport.width, containerHeight / viewport.height);
    const scaledViewport = page.getViewport({ scale });

    canvas.width = scaledViewport.width;
    canvas.height = scaledViewport.height;

    const renderContext = {
      canvasContext: context,
      viewport: scaledViewport
    };

    renderTasks[pdfIndex] = page.render(renderContext);
    renderTasks[pdfIndex].promise.then(function () {
      renderTasks[pdfIndex] = null;
    });
  }).catch(error => {
    console.error(`Fehler beim Anzeigen der Seite ${pageNum} für PDF ${pdfIndex}:`, error);
  });
}

// Funktion zum Wechseln zur nächsten Seite
function nextPage(pdfIndex) {
  if (currentPages[pdfIndex] < pdfDocuments[pdfIndex].numPages) {
    currentPages[pdfIndex]++;
  } else {
    currentPages[pdfIndex] = 1;
  }
  displayPage(pdfIndex, currentPages[pdfIndex]);
}

// PDFs initial laden
loadPdfs();

// Seitenwechsel alle 15 Sekunden
for (let i = 0; i < totalPdfs; i++) {
  setInterval(() => nextPage(i), intervalTimes[i]);
}

// PDFs alle 1 Minute neu laden
setInterval(() => {
  console.log("PDFs werden neu geladen...");
  loadPdfs();
}, reloadInterval);

// Seiten bei Fenstergröße ändern neu rendern
window.addEventListener('resize', () => {
  for (let i = 0; i < totalPdfs; i++) {
    displayPage(i, currentPages[i]);
  }
});

function loadWeatherData() {
  fetch('output/wetterdaten.json')
    .then(response => response.json())
    .then(data => {
      document.getElementById('weather').innerText = `${data.weather}, ${data.akt_temperature}`;
      document.getElementById('weather-icon').src = `output/wetter_icon.png`;
      document.getElementById('min-temp').innerText = `Min: ${data.min_temperature}`;
      document.getElementById('max-temp').innerText = `Max: ${data.max_temperature}`;
    })
    .catch(error => console.error('Fehler beim Laden der Wetterdaten:', error));

  fetch('output/wettervorhersage.json')
    .then(response => response.json())
    .then(data => {
      const forecastContainer = document.getElementById('forecast-container');
      forecastContainer.innerHTML = ''; // Clear previous content

      data.slice(0, 7).forEach(day => {
        const dayElement = document.createElement('div');
        dayElement.className = 'forecast-day';

        const dateElement = document.createElement('p');
        dateElement.innerText = new Date(day.date).toLocaleDateString('de-DE', { weekday: 'short' });

        const iconElement = document.createElement('img');
        iconElement.src = `output/${day.date}.png`; // Verwende das passende Bild aus dem output-Ordner

        const tempElement = document.createElement('p');
        tempElement.innerText = `${day.min_temperature} / ${day.max_temperature}`;

        dayElement.appendChild(dateElement);
        dayElement.appendChild(iconElement);
        dayElement.appendChild(tempElement);

        forecastContainer.appendChild(dayElement);
      });
    })
    .catch(error => console.error('Fehler beim Laden der Wettervorhersage:', error));
}

function updateWeatherData() {
  loadWeatherData();
  setInterval(loadWeatherData, 3600000); // Aktualisiert die Wetterdaten jede Stunde
}

function loadMarqueeData() {
  fetch('output/infos.json')
    .then(response => response.json())
    .then(data => {
      const marquee1 = document.getElementById('marquee1').querySelector('p');

      // Beispiel: Zeige die ersten beiden Infos aus der JSON-Datei an
      marquee1.textContent = data.infos;
    })
    .catch(error => console.error('Fehler beim Laden der Marquee-Daten:', error));
}


window.addEventListener('load', () => {
  loadWeatherData();
  updateWeatherData();
  loadMarqueeData();
  setInterval(loadMarqueeData, 60000); // Aktualisiert die Marquee-Daten jede Minute
});