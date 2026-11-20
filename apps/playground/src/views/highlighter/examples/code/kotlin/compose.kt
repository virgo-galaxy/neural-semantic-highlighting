import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@Composable
fun CounterCard(title: String) {
    var count by remember { mutableStateOf(0) }

    Column(modifier = Modifier.padding(24.dp)) {
        Text(text = title)
        Text(text = "Count: $count")
        Button(onClick = { count += 1 }) {
            Text("Add one")
        }
    }
}
