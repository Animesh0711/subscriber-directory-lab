// The original Python algorithms run off the UI thread.
const ready = (async () => {
  importScripts('https://cdn.jsdelivr.net/pyodide/v0.28.1/full/pyodide.js');
  const py = await loadPyodide();
  py.FS.mkdirTree('/project/source');
  py.FS.mkdirTree('/project/data');
  py.FS.mkdirTree('/project/results');
  const names = ['metrics','data_io','skip_list','hash_table','sorted_array','controller','benchmark','tests'];
  await Promise.all(names.map(async name => {
    const response = await fetch('./source/'+name+'.py');
    if (!response.ok) throw Error('Could not load '+name);
    py.FS.writeFile('/project/source/'+name+'.py',await response.text());
  }));
  const bridge = await fetch('./bridge.py');
  if (!bridge.ok) throw Error('Could not load browser adapter');
  await py.runPythonAsync(await bridge.text());
  return py;
})();
// Handle initialization failure when the first request arrives.
ready.catch(()=>{});
let queue=Promise.resolve();
self.onmessage=({data: request})=>{
  queue=queue.then(async()=>{
    try {
      const py=await ready;
      py.globals.set('request_json',JSON.stringify(request));
      const result=JSON.parse(await py.runPythonAsync('dispatch(request_json)'));
      self.postMessage({id:request.id,result});
    } catch(error) {
      self.postMessage({id:request.id,error:String(error.message || error)});
    }
  });
};
