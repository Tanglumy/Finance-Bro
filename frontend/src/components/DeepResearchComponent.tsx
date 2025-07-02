import { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { AnalysisComponent } from "./AnalysisComponent";
import { Brain, Search } from "lucide-react";

export function DeepResearchComponent() {
  const [activeTab, setActiveTab] = useState("analysis");

  return (
    <div className="space-y-6">
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-2 mb-6 bg-slate-800/50 border border-slate-700">
          <TabsTrigger 
            value="analysis" 
            className="flex items-center space-x-2 data-[state=active]:bg-emerald-600 data-[state=active]:text-white"
          >
            <Brain className="h-4 w-4" />
            <span>AI Analysis</span>
          </TabsTrigger>
          <TabsTrigger 
            value="research" 
            className="flex items-center space-x-2 data-[state=active]:bg-blue-600 data-[state=active]:text-white"
          >
            <Search className="h-4 w-4" />
            <span>Deep Research (Coming Soon)</span>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="analysis" className="mt-0">
          <AnalysisComponent />
        </TabsContent>

        <TabsContent value="research" className="mt-0">
          <div className="text-center py-12">
            <Search className="h-16 w-16 mx-auto mb-4 text-slate-600" />
            <h3 className="text-xl font-semibold text-slate-400 mb-2">Advanced Research Engine</h3>
            <p className="text-slate-500">Coming soon: Event-driven deep research with real-time market analysis</p>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}