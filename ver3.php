<?php
	require_once ("config/db.php");
    require_once ("config/conexion.php");
	include 'funciones2.php';

	$user = $_GET['val'];
	$val = $_GET['val1'];

	//print_r($_POST);
	if ($val != 0){
		$val = 1;
	}else{
		$val = 0;
	}

	//echo $val;
	//foreach($_POST as $campo => $valor){
	//	if (!empty($valor)){
	//		 echo " | ". $campo ." = ". $valor;
	//		 echo "<br>";
	//	}
	//}
	//echo "<br>";
		


	foreach($_POST as $campo => $valor){
		
		if ($campo[0] == '*' && !empty($valor)){

			$mes = extraer_mes($campo);
			//echo $mes;
			//echo "<br>";
			//$fecha = "2020-12-1"; //fecha inicial para sumar el numero de mes
			if ($val != 0){
				$fecha = "2021-12-1"; //fecha inicial para sumar el numero de mes
			}else{
				$fecha = "2021-12-1"; //fecha inicial para sumar el numero de mes
			}
	  		$fecha = date('Y-m-d',strtotime($fecha."+".$mes. "month"));
			$categoria = extraer_categoria($campo);
			///echo "<br>"; 
			$prod = extraer_prod($campo);
			//echo "<br>";
			$valor = floatval($valor);

			//echo "<br>";
			//printf("fecha: %s - prod: %s - valor: %d <br>", $fecha, $prod, $valor);
			$query ="INSERT INTO movimientos (IdMovimiento, Fecha,Comercio,Producto,Categoria, Cantidad, Total, Tipo, Adjunto, Usuario) VALUES ('0','$fecha',28,$prod, $categoria ,1,$valor,1,'0',$user)";
			//echo "new <br>";
			mysqli_query($con, $query);
			
		}

		if ($campo[0] == '!' && !empty($valor)){
			
			$mes = extraer_mes2($campo);
			$hoy = intval(date('m'));
			if ($val != 0){
				$anio = 2022;
			}else{
				$anio = 2021;
			}
			
			if ($val != 0){
				$fecha = "2021-12-1"; //fecha inicial para sumar el numero de mes
			}else{
				$fecha = "2021-12-1"; //fecha inicial para sumar el numero de mes
			}
	  		$fecha = date('Y-m-d',strtotime($fecha."+".$mes. "month"));
	  		$item = extraer_item($campo);

			$ingreso = $valor;  		

			$query_20 = "SELECT sum(Total) FROM movimientos WHERE Tipo = 2 AND YEAR(Fecha) = '$anio' AND MONTH(Fecha) = '$mes' AND Usuario = $user";

 			if ($mes > $hoy){
 				$query_20 = "SELECT sum(Total) FROM movimientos WHERE Tipo = 1 AND YEAR(Fecha) = '$anio' AND MONTH(Fecha) = '$mes' AND Usuario = $user";
 			}
	  		//echo $query_20;
	      	//echo "<br>";
	        $datos02 = mysqli_query($con,$query_20);
	        $row20 = mysqli_fetch_array($datos02, MYSQLI_ASSOC);
 			$gastos = floatval($row20['sum(Total)']);
 			if ($gastos < 0){
 				$gastos = -$gastos;
 			}
	        

	        $ahorro = $ingreso - $gastos;
	        if ($ahorro < 0){
 				$ahorro = - $ahorro;
 			}
	        //echo $ahorro;
	        //echo "<br>";
 			if ($ahorro < 0){
 				$ahorro = - $ahorro;
 			}
 			
 		}

  		if ($campo[0] == '#' && !empty($valor)){
			
			$mes = extraer_mes3($campo);
			$hoy = intval(date('m'));
			if ($val != 0){
				$anio = 2022;
			}else{
				$anio = 2021;
			}
			if ($val != 0){
				$fecha = "2021-12-1"; //fecha inicial para sumar el numero de mes
			}else{
				$fecha = "2021-12-1"; //fecha inicial para sumar el numero de mes
			}
	  		$fecha = date('Y-m-d',strtotime($fecha."+".$mes. "month"));		

			$query_20 = "INSERT INTO `saldo`(`idSaldo`, `Fecha`, `Saldo`) VALUES ('0','$fecha',$valor)";
			//echo $query_20;
			mysqli_query($con, $query_20);
			
		}

		if ($campo[0] != '*' && $campo[0] != '@'){
			
			$id_mov = intval($campo);
			$valor = floatval($valor);
			
			$query2 = "UPDATE movimientos SET Total=$valor WHERE IdMovimiento = $id_mov";
			//echo "id <br>";
			mysqli_query($con, $query2);

			if ($valor == 0){
				$query3 = "DELETE FROM `movimientos` WHERE IdMovimiento = $id_mov";
				//echo "id <br>";
				mysqli_query($con, $query3);
			}
		}




		if ($campo[0] == '@'){
			//printf("campo %s, valor %s: ", $campo, $valor);
			//echo "<br>";
			$id = extraer_id($campo);
			$valor24 = floatval($valor);
			//printf("campo %s, valor %s: ", $id, $valor24);
	      	//echo "<br>";
			$query_1 = "SELECT month(Fecha) from ahorros where idAhorro = $id";
			$datos_1 = mysqli_query($con, $query_1);
			$row_1 = mysqli_fetch_array($datos_1, MYSQLI_ASSOC);
			$mes = $row_1['month(Fecha)'];
			//echo $mes;
			//echo "<br>";
			$hoy = intval(date('m'));
			if ($val != 0){
				$anio = 2022;
			}else{
				$anio = 2021;
			}
			
	  		 //printf("valor2@@@ %s: ",$valor24);
	      	//echo "<br>";		

			$query_20 = "SELECT sum(Total) FROM movimientos WHERE Tipo = 2 AND YEAR(Fecha) = '$anio' AND MONTH(Fecha) = '$mes' AND Usuario = $user";

 			if ($mes > $hoy){
 				$query_20 = "SELECT sum(Total) FROM movimientos WHERE Tipo = 1 AND YEAR(Fecha) = '$anio' AND MONTH(Fecha) = '$mes' AND Usuario = $user";
 			}
	  		//printf("valor2!!! %s ",$valor24);
	      	//echo "<br>";
	        $datos02 = mysqli_query($con,$query_20);
	        $row20 = mysqli_fetch_array($datos02, MYSQLI_ASSOC);
	        $gastos = $row20['sum(Total)'];
 			if ($gastos < 0){
 				$gastos = -$gastos;
 			}
	        $ahorro =round( $valor24 - floatval($gastos),2);
	        //echo $ahorro;
	        //echo "<br>";


			$query2 = "UPDATE ahorros SET Ingreso = $valor, Ahorro = $ahorro WHERE idAhorro = $id";
			//echo $query2;
			//echo "<br>";
			mysqli_query($con, $query2);


			//echo $query2;
			//echo "<br>";
			if ($valor == 0){
				$query3 = "DELETE FROM `ahorros` WHERE idAhorro = $id";
				//echo "id <br>";
				mysqli_query($con, $query3);
			}
		}

		if ($campo[0] == '%'){
			//printf("campo %s, valor %s: ", $campo, $valor);
			//echo "<br>";
			$id = extraer_id($campo);
			$valor24 = floatval($valor);
			//printf("campo %s, valor %s: ", $id, $valor24);
	      	//echo "<br>";
			$query_1 = "SELECT month(Fecha) from saldo where idSaldo = $id";
			$datos_1 = mysqli_query($con, $query_1);
			$row_1 = mysqli_fetch_array($datos_1, MYSQLI_ASSOC);
			$mes = $row_1['month(Fecha)'];
			//echo $mes;
			//echo "<br>";
			$hoy = intval(date('m'));
			if ($val != 0){
				$anio = 2022;
			}else{
				$anio = 2021;
			}
	  		

			$query2 = "UPDATE saldo SET Saldo = $valor WHERE idSaldo = $id";
			//echo $query2;
			//echo "<br>";
			mysqli_query($con, $query2);


			//echo $query2;
			//echo "<br>";
			if ($valor == 0){
				$query3 = "DELETE FROM saldo WHERE idSaldo = $id";
				//echo "id <br>";
				mysqli_query($con, $query3);
			}
		}
	}
	if ($val != 0){
		$anio = 2022;
	}else{
		$anio = 2021;
	}

	secargo4($user,$anio);
?>