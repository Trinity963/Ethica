function testBug() {
  const data = [1, 2, 3];
  console.log(data.map(x => x.toUpperCase())); // ERROR: numbers don’t have toUpperCase
}
testBug();
throw new Error("Simulated fault");
