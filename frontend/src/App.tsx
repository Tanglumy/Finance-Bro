import { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { DeepResearchComponent } from "@/components/DeepResearchComponent";
import { FinanceNewsComponent } from "@/components/FinanceNewsComponent";
import { RewardsAgentComponent } from "@/components/RewardsAgentComponent";
import { ExecutiveAgentComponent } from "@/components/ExecutiveAgentComponent";
import { TrendingUp, Brain, Newspaper, Trophy } from "lucide-react";

export default function App() {
  const [activeTab, setActiveTab] = useState("research");

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 text-white">
      <header className="border-b border-slate-700 bg-slate-900/50 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <TrendingUp className="h-8 w-8 text-emerald-400" />
              <h1 className="text-2xl font-bold bg-gradient-to-r from-emerald-400 to-blue-400 bg-clip-text text-transparent">
                Finance Bro
              </h1>
            </div>
            <div className="text-sm text-slate-400">
              Your AI-Powered Investment Assistant
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-6">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-4 mb-6 bg-slate-800/50 border border-slate-700">
            <TabsTrigger 
              value="research" 
              className="flex items-center space-x-2 data-[state=active]:bg-emerald-600 data-[state=active]:text-white"
            >
              <Brain className="h-4 w-4" />
              <span>Deep Research</span>
            </TabsTrigger>
            <TabsTrigger 
              value="news" 
              className="flex items-center space-x-2 data-[state=active]:bg-blue-600 data-[state=active]:text-white"
            >
              <Newspaper className="h-4 w-4" />
              <span>Finance News</span>
            </TabsTrigger>
            <TabsTrigger 
              value="rewards" 
              className="flex items-center space-x-2 data-[state=active]:bg-purple-600 data-[state=active]:text-white"
            >
              <Trophy className="h-4 w-4" />
              <span>Portfolio Rewards</span>
            </TabsTrigger>
            <TabsTrigger 
              value="executive" 
              className="flex items-center space-x-2 data-[state=active]:bg-orange-600 data-[state=active]:text-white"
            >
              <TrendingUp className="h-4 w-4" />
              <span>Executive Agent</span>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="research" className="mt-0">
            <DeepResearchComponent />
          </TabsContent>

          <TabsContent value="news" className="mt-0">
            <FinanceNewsComponent />
          </TabsContent>

          <TabsContent value="rewards" className="mt-0">
            <RewardsAgentComponent />
          </TabsContent>

          <TabsContent value="executive" className="mt-0">
            <ExecutiveAgentComponent />
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
