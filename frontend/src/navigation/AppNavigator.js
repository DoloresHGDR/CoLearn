import { NavigationContainer } from "@react-navigation/native";
import { createStackNavigator } from "@react-navigation/stack";
import React from "react";
import ChatScreen from "../screens/ChatScreen";
import CreateClassScreen from "../screens/CreateClassScreen";
import HomeScreen from "../screens/HomeScreen";
import JoinClassScreen from "../screens/JoinClassScreen";
import LoginScreen from "../screens/LoginScreen";
import MetricsScreen from "../screens/MetricsScreen";
import RegisterScreen from "../screens/RegisterScreen";
import TeacherQuestionsScreen from "../screens/TeacherQuestionsScreen";
import { colors } from "../styles/theme";

const Stack = createStackNavigator();

// Opciones de cabecera compartidas
const headerOptions = {
  headerStyle: { backgroundColor: colors.white },
  headerTintColor: colors.primary,
  headerTitleStyle: { fontWeight: "700", color: colors.text },
  headerBackTitleVisible: false,
};

export default function AppNavigator() {
  return (
    <NavigationContainer>
      <Stack.Navigator initialRouteName="Login" screenOptions={headerOptions}>
        <Stack.Screen name="Login" component={LoginScreen} options={{ headerShown: false }} />
        <Stack.Screen name="Register" component={RegisterScreen} options={{ title: "Registro" }} />
        <Stack.Screen name="Home" component={HomeScreen} options={{ title: "CoLearn", headerLeft: null }} />
        <Stack.Screen name="CreateClass" component={CreateClassScreen} options={{ title: "Nueva clase" }} />
        <Stack.Screen name="JoinClass" component={JoinClassScreen} options={{ title: "Unirse a clase" }} />
        <Stack.Screen
          name="Chat"
          component={ChatScreen}
          options={({ route }) => ({ title: route.params?.className || "Chat" })}
        />
        <Stack.Screen
          name="Metrics"
          component={MetricsScreen}
          options={({ route }) => ({ title: route.params?.className || "Métricas" })}
        />
        <Stack.Screen
          name="TeacherQuestions"
          component={TeacherQuestionsScreen}
          options={{ title: "Preguntas de la IA" }}
        />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
